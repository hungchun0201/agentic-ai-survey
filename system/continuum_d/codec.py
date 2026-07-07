# SPDX-License-Identifier: Apache-2.0
"""KV quantize-on-offload codec for Continuum-D (precision-as-admission-currency).

This is the MECHANISM that turns KV *precision* into a per-block offload action:
when the residency scheduler decides to push a finished-turn KV block out of HBM,
it may first *compress* that block to fp8 or int4 before the DRAM copy, and
*dequantize* it back to fp16 on reload. The compressed block occupies less DRAM
AND costs less PCIe on reload (the win); the only price is the round-trip
quantization error (accuracy loss), which the joint policy weighs per block.

No mixed-precision attention kernel is needed: blocks live compressed *only while
resident in DRAM*, and are dequantized back to the model dtype before they
re-enter the KV cache, so attention always sees fp16 (dequant-on-reload).

Codecs (all operate on a real KV block tensor of shape (..., head_dim)):
  * FP16  passthrough (the fp16-offload / keep-resident baseline precision)
  * FP8   native torch float8_e4m3fn with a per-token amax scale (the vLLM
          "FP8 KV cache" recipe). 2x smaller than fp16.
  * INT4  group-wise symmetric int4, KIVI recipe: keys quantized along the
          channel axis, values along the token axis (per-block we expose the
          axis as a parameter). ~3.5x smaller than fp16 including fp16 scales.

Everything here is device-agnostic (CPU or CUDA) and dtype-honest: `dram_bytes`
and `CompressedBlock.nbytes` count the *actual* resident payload (packed data +
scales), so the DRAM-reduction claim is measured, not assumed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

import torch


class Precision(str, Enum):
    """The precision an offloaded KV block is stored at while resident in DRAM."""

    FP16 = "fp16"
    FP8 = "fp8"
    INT4 = "int4"


# Nominal bytes-per-element for the *data* payload (scales counted separately).
_DATA_BYTES_PER_ELEM: dict[Precision, float] = {
    Precision.FP16: 2.0,
    Precision.FP8: 1.0,
    Precision.INT4: 0.5,
}

# Compression ratio vs fp16 (data only, ignoring the small scale overhead).
# Used by the policy's cost model; the *measured* ratio (with scales) comes from
# CompressedBlock.nbytes and is always slightly worse than this nominal number.
NOMINAL_RATIO: dict[Precision, float] = {
    Precision.FP16: 1.0,
    Precision.FP8: 0.5,
    Precision.INT4: 0.25,
}


def dram_bytes(nelem: int, precision: Precision, group_size: int = 64) -> int:
    """Resident DRAM bytes for `nelem` KV elements stored at `precision`.

    Includes the fp16 scale overhead for the lossy codecs so the number matches
    what `CompressedBlock.nbytes` reports after a real compress().
    """
    data = int(math.ceil(nelem * _DATA_BYTES_PER_ELEM[precision]))
    if precision is Precision.FP16:
        return data
    if precision is Precision.FP8:
        # one fp16 scale per token-row; approximate as nelem/group_size rows.
        scale = 2 * int(math.ceil(nelem / max(group_size, 1)))
        return data + scale
    # INT4: one fp16 scale per group.
    scale = 2 * int(math.ceil(nelem / max(group_size, 1)))
    return data + scale


@dataclass
class CompressedBlock:
    """A KV block compressed for DRAM residency.

    `data` + `scales` are the *only* tensors that occupy DRAM; `nbytes` is the
    real resident footprint. `decompress()` reconstructs the fp16 block.
    """

    precision: Precision
    data: torch.Tensor  # packed payload (fp8 dtype, or int8 nibble-packed)
    scales: torch.Tensor | None  # fp16 per-group/per-token scales (None for fp16)
    shape: tuple[int, ...]  # original block shape
    dtype: torch.dtype  # original dtype (restored on decompress)
    axis: int  # quant group axis (KIVI: -1 for keys/channel, token-axis for values)
    group_size: int

    @property
    def nbytes(self) -> int:
        n = self.data.element_size() * self.data.nelement()
        if self.scales is not None:
            n += self.scales.element_size() * self.scales.nelement()
        return n


def _quantize_int4_symmetric(
    x: torch.Tensor, axis: int, group_size: int
) -> tuple[torch.Tensor, torch.Tensor]:
    """Group-wise symmetric int4 quant along `axis`. Returns (codes int8, scales).

    codes are in [-7, 7] stored one-per-int8 (packing to nibbles happens in
    `compress`). scales are fp16, one per group.
    """
    x = x.movedim(axis, -1)  # group axis to last
    lead = x.shape[:-1]
    n = x.shape[-1]
    pad = (group_size - n % group_size) % group_size
    if pad:
        x = torch.nn.functional.pad(x, (0, pad))
    g = x.shape[-1] // group_size
    xg = x.reshape(*lead, g, group_size).to(torch.float32)
    amax = xg.abs().amax(dim=-1, keepdim=True).clamp_(min=1e-8)
    scale = amax / 7.0
    codes = torch.round(xg / scale).clamp_(-7, 7).to(torch.int8)
    codes = codes.reshape(*lead, g * group_size)
    return codes, scale.squeeze(-1).to(torch.float16)


def _dequantize_int4_symmetric(
    codes: torch.Tensor,
    scales: torch.Tensor,
    axis: int,
    group_size: int,
    orig_len: int,
    dtype: torch.dtype,
) -> torch.Tensor:
    lead = codes.shape[:-1]
    g = codes.shape[-1] // group_size
    cg = codes.reshape(*lead, g, group_size).to(torch.float32)
    x = (cg * scales.unsqueeze(-1).to(torch.float32)).reshape(*lead, g * group_size)
    x = x[..., :orig_len]
    return x.movedim(-1, axis).to(dtype).contiguous()


def _pack_nibbles(codes: torch.Tensor) -> torch.Tensor:
    """Pack signed int4 codes ([-7,7]) two-per-byte into a flat int8 tensor."""
    flat = codes.reshape(-1).to(torch.int16)
    flat = (flat & 0x0F).to(torch.uint8)  # 4-bit two's complement
    if flat.numel() % 2:
        flat = torch.cat([flat, flat.new_zeros(1)])
    lo = flat[0::2]
    hi = flat[1::2]
    return ((hi << 4) | lo).to(torch.int8)


def _unpack_nibbles(packed: torch.Tensor, n: int) -> torch.Tensor:
    """Inverse of `_pack_nibbles`; returns `n` signed int8 codes in [-7,7]."""
    p = packed.to(torch.uint8)
    lo = (p & 0x0F).to(torch.int16)
    hi = ((p >> 4) & 0x0F).to(torch.int16)
    out = torch.stack([lo, hi], dim=1).reshape(-1)[:n]
    # sign-extend 4-bit two's complement
    out = torch.where(out >= 8, out - 16, out)
    return out.to(torch.int8)


def _fp8_supported(device: torch.device) -> bool:
    try:
        torch.zeros(2, dtype=torch.float16, device=device).to(torch.float8_e4m3fn)
        return True
    except Exception:
        return False


# max representable magnitude of float8_e4m3fn
_FP8_AMAX = 448.0


def compress(
    block: torch.Tensor,
    precision: Precision,
    axis: int = -1,
    group_size: int = 64,
) -> CompressedBlock:
    """Compress a KV block to `precision`. `axis` is the KIVI group axis.

    For KEYS use axis=-1 (per-channel); for VALUES use the token axis. FP16
    returns a passthrough (still a CompressedBlock so the store path is uniform).
    """
    orig_shape = tuple(block.shape)
    orig_dtype = block.dtype

    if precision is Precision.FP16:
        return CompressedBlock(
            precision, block.detach().to(torch.float16), None,
            orig_shape, orig_dtype, axis, group_size,
        )

    if precision is Precision.FP8:
        x = block.movedim(axis, -1).to(torch.float32)
        amax = x.abs().amax(dim=-1, keepdim=True).clamp_(min=1e-8)
        scale = (amax / _FP8_AMAX).to(torch.float16)
        if _fp8_supported(block.device):
            q = (x / scale.to(torch.float32)).clamp_(-_FP8_AMAX, _FP8_AMAX)
            data = q.to(torch.float8_e4m3fn)
        else:
            # CPU fallback: emulate the e4m3 round-trip in fp16 but still store 1
            # byte/elem (uint8) so the DRAM footprint is honest.
            q = (x / scale.to(torch.float32)).clamp_(-_FP8_AMAX, _FP8_AMAX)
            # crude e4m3 requantization via fp16 (adequate for a smoke/error bound)
            data = _emulate_e4m3_to_uint8(q)
        data = data.movedim(-1, axis).contiguous()
        # `scale` is already in the axis-moved frame (group axis last); store it
        # squeezed so decompress can `unsqueeze(-1)` after the same movedim.
        return CompressedBlock(
            precision, data, scale.squeeze(-1).contiguous(),
            orig_shape, orig_dtype, axis, group_size,
        )

    # INT4 (KIVI group-wise symmetric). Clamp the group to the axis length so a
    # short quant axis (e.g. a 16-token block quantized per-channel) never pads
    # up to a large group_size and inflates the footprint above fp16.
    eff_gs = min(group_size, orig_shape[axis])
    codes, scales = _quantize_int4_symmetric(block, axis, eff_gs)
    packed = _pack_nibbles(codes)
    return CompressedBlock(
        precision, packed, scales, orig_shape, orig_dtype, axis, eff_gs,
    )


def decompress(cb: CompressedBlock) -> torch.Tensor:
    """Reconstruct the fp16 (original-dtype) KV block from a CompressedBlock."""
    if cb.precision is Precision.FP16:
        return cb.data.to(cb.dtype)

    if cb.precision is Precision.FP8:
        if cb.data.dtype == torch.float8_e4m3fn:
            x = cb.data.movedim(cb.axis, -1).to(torch.float32)
        else:
            x = _emulate_e4m3_from_uint8(cb.data.movedim(cb.axis, -1))
        x = x * cb.scales.unsqueeze(-1).to(torch.float32)
        return x.movedim(-1, cb.axis).to(cb.dtype).contiguous()

    # INT4
    x = cb.block_view_for_int4()
    return x


def _emulate_e4m3_to_uint8(q: torch.Tensor) -> torch.Tensor:
    """CPU-only fp8 e4m3 emulation: quantize mantissa to 3 bits, store as uint8.

    Not bit-exact to hardware e4m3 but a faithful 8-bit-with-3-mantissa-bit
    round-trip for error bounding; footprint is a true 1 byte/elem.
    """
    sign = (q < 0).to(torch.uint8)
    a = q.abs().clamp_(min=2**-9, max=_FP8_AMAX)
    e = torch.floor(torch.log2(a)).clamp_(-6, 8)
    frac = a / torch.pow(2.0, e)  # in [1,2)
    mant = torch.round((frac - 1.0) * 8).clamp_(0, 7).to(torch.uint8)  # 3 bits
    ebits = (e + 7).clamp_(0, 15).to(torch.uint8)  # bias 7, 4 bits
    return (sign << 7) | (ebits << 3) | mant


def _emulate_e4m3_from_uint8(p: torch.Tensor) -> torch.Tensor:
    p = p.to(torch.int32)
    sign = ((p >> 7) & 0x1).to(torch.float32)
    ebits = ((p >> 3) & 0x0F).to(torch.float32)
    mant = (p & 0x07).to(torch.float32)
    val = (1.0 + mant / 8.0) * torch.pow(2.0, ebits - 7)
    return torch.where(sign > 0, -val, val)


def _int4_block_view(cb: CompressedBlock) -> torch.Tensor:
    lead_axis_len = cb.shape[cb.axis]
    # reconstruct code tensor shape (leading dims with group axis moved last)
    moved = list(cb.shape)
    axis = cb.axis if cb.axis >= 0 else len(cb.shape) + cb.axis
    lead = moved[:axis] + moved[axis + 1 :]
    n = lead_axis_len
    g = (n + cb.group_size - 1) // cb.group_size
    total_codes = int(torch.tensor(lead).prod().item()) * g * cb.group_size if lead else g * cb.group_size
    codes = _unpack_nibbles(cb.data, total_codes)
    codes = codes.reshape(*lead, g * cb.group_size)
    return _dequantize_int4_symmetric(
        codes, cb.scales, cb.axis, cb.group_size, n, cb.dtype
    )


# attach the int4 view as a method (kept out of the dataclass body for clarity)
CompressedBlock.block_view_for_int4 = lambda self: _int4_block_view(self)  # type: ignore[attr-defined]


def roundtrip_error(block: torch.Tensor, precision: Precision, axis: int = -1,
                    group_size: int = 64) -> dict:
    """Measure the compress->decompress error + real DRAM footprint of a block."""
    cb = compress(block, precision, axis=axis, group_size=group_size)
    rec = decompress(cb)
    ref = block.to(torch.float32)
    err = (rec.to(torch.float32) - ref)
    denom = ref.norm().clamp_(min=1e-8)
    fp16_bytes = block.nelement() * 2
    return {
        "precision": precision.value,
        "rel_l2": (err.norm() / denom).item(),
        "max_abs": err.abs().max().item(),
        "rmse": err.pow(2).mean().sqrt().item(),
        "resident_bytes": cb.nbytes,
        "fp16_bytes": fp16_bytes,
        "measured_ratio": cb.nbytes / max(fp16_bytes, 1),
    }
