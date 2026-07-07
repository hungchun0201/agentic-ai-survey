# SPDX-License-Identifier: Apache-2.0
"""CPU-only unit tests for the quantize-on-offload KV codec (no GPU needed).

Run: PYTHONPATH=<agent-kvcache>/.pylib python -m pytest continuum_d/tests/ -q
"""
import torch

from continuum_d.codec import (
    Precision,
    compress,
    decompress,
    dram_bytes,
    roundtrip_error,
)


def _kv_block(tokens=16, heads=8, head_dim=128, scale=3.0, seed=0):
    g = torch.Generator().manual_seed(seed)
    return (torch.randn(tokens, heads, head_dim, generator=g) * scale).to(torch.float16)


def test_fp16_passthrough_is_exact():
    blk = _kv_block()
    cb = compress(blk, Precision.FP16)
    rec = decompress(cb)
    assert torch.equal(rec.to(torch.float16), blk)
    assert cb.nbytes == blk.nelement() * 2


def test_fp8_halves_dram_with_bounded_error():
    blk = _kv_block()
    r = roundtrip_error(blk, Precision.FP8, axis=-1)
    assert r["measured_ratio"] < 0.60, r  # ~0.5 + scale overhead
    assert r["rel_l2"] < 0.05, r          # fp8 e4m3 is ~2-3% rel L2 on N(0,3)


def test_int4_kivi_shrinks_below_third_with_bounded_error():
    blk = _kv_block()
    # values: per-token (group along head_dim, axis=-1)
    rv = roundtrip_error(blk, Precision.INT4, axis=-1)
    assert rv["measured_ratio"] < 0.35, rv
    assert rv["rel_l2"] < 0.20, rv
    # keys: per-channel (group along the token axis=0)
    rk = roundtrip_error(blk, Precision.INT4, axis=0)
    assert rk["measured_ratio"] < 0.40, rk
    assert rk["rel_l2"] < 0.20, rk


def test_ordering_fp16_gt_fp8_gt_int4_bytes():
    blk = _kv_block()
    b16 = compress(blk, Precision.FP16).nbytes
    b8 = compress(blk, Precision.FP8, axis=-1).nbytes
    b4 = compress(blk, Precision.INT4, axis=-1).nbytes
    assert b16 > b8 > b4


def test_dram_bytes_matches_measured():
    blk = _kv_block()
    for p in (Precision.FP8, Precision.INT4):
        cb = compress(blk, p, axis=-1, group_size=64)
        est = dram_bytes(blk.nelement(), p, group_size=64)
        # estimate within 30% of the real packed footprint (scale-count rounding)
        assert 0.7 * cb.nbytes <= est <= 1.3 * cb.nbytes, (p, est, cb.nbytes)


def test_roundtrip_shape_and_dtype_preserved():
    for shp, axis in [((16, 8, 128), -1), ((16, 8, 128), 0), ((32, 1024), -1)]:
        blk = _kv_block(*(shp + (0, 0))[:3]) if len(shp) == 3 else (
            torch.randn(*shp) * 3).to(torch.float16)
        for p in (Precision.FP8, Precision.INT4):
            rec = decompress(compress(blk, p, axis=axis))
            assert tuple(rec.shape) == shp
            assert rec.dtype == torch.float16
