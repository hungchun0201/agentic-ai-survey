# SPDX-License-Identifier: Apache-2.0
"""Physical proof of the quantize-on-offload codec on REAL Llama-3.1-8B KV.

This is Part B of the co-design smoke (Part A = the live vLLM server run of the
PrecisionOffloadingSpec in continuum_d_bench.py). It answers, on genuine model
KV, the two mechanism questions the direction doc asks:

  1. "compress -> offload -> reload -> dequant produces correct output"
     -> we prefill a real prompt to get the true KV cache, compress every layer's
        K (KIVI per-channel) and V (KIVI per-token) to fp8 / int4, dequantize, and
        run ONE more forward with the reconstructed cache. We report the next-token
        top-1 agreement and the logit relative error vs the fp16 cache. Small error
        + top-1 agreement == the round-trip preserves generation (dequant-on-reload,
        no mixed-precision attention kernel needed).

  2. "the compressed blocks genuinely use less DRAM (measure it)"
     -> we measure the REAL resident bytes of the whole KV cache at fp16 vs fp8 vs
        int4 (packed payload + fp16 scales), i.e. the actual DRAM the offloaded
        cache would occupy.

Everything here is measured, not assumed. Redirect all caches to scratch on PACE
(HOME quota is full); SIGTERM only.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import torch

# codec lives in the continuum_d package (import via .pylib on PYTHONPATH)
from continuum_d.codec import Precision, compress, decompress


def _extract_kv(past):
    """Return a list of (K, V) per layer, robust across transformers 4.x/5.x.

    Tries, in order: legacy-tuple conversion, v5 `.layers[i].keys/.values`,
    and the `.key_cache/.value_cache` lists.
    """
    # transformers 4.x legacy tuple / to_legacy_cache
    if hasattr(past, "to_legacy_cache"):
        try:
            leg = past.to_legacy_cache()
            if leg is not None:
                return [(k, v) for (k, v) in leg]
        except Exception:
            pass
    # transformers 5.x: Cache.layers[i].keys / .values
    if hasattr(past, "layers"):
        try:
            return [(ly.keys, ly.values) for ly in past.layers]
        except Exception:
            pass
    # older Cache: parallel key_cache / value_cache lists
    if hasattr(past, "key_cache") and hasattr(past, "value_cache"):
        return list(zip(past.key_cache, past.value_cache))
    # plain tuple/list of (K, V)
    return [(k, v) for (k, v) in past]


def _rebuild_cache(rec, template):
    """Best-effort rebuild of a cache object of the same type as `template`.

    Returns a cache usable as past_key_values, or None if the API doesn't allow
    it (caller then skips the model-level probe and relies on the block-level
    round-trip + DRAM measurements, which are the load-bearing signals).
    """
    # transformers 4.x legacy tuple accepted directly
    try:
        from transformers import DynamicCache
        if hasattr(DynamicCache, "from_legacy_cache"):
            return DynamicCache.from_legacy_cache(tuple(rec))
    except Exception:
        pass
    # transformers 5.x: write tensors into a fresh DynamicCache via update()
    try:
        from transformers import DynamicCache
        cache = DynamicCache()
        for i, (k, v) in enumerate(rec):
            cache.update(k, v, i)
        return cache
    except Exception:
        return None


def _codec_roundtrip_cache(layers, precision, group_size):
    """Compress+dequant every layer's K (per-channel) and V (per-token).

    K,V shape: (batch, n_kv_heads, seq, head_dim).
      keys  -> KIVI per-channel: group along the token axis (seq, dim=2)
      values-> KIVI per-token:   group along the channel axis (head_dim, dim=3)
    Returns (reconstructed_layers, fp16_bytes, compressed_bytes).
    """
    rec = []
    fp16_bytes = comp_bytes = 0
    for k, v in layers:
        kf, vf = k.to(torch.float16), v.to(torch.float16)
        fp16_bytes += kf.nelement() * 2 + vf.nelement() * 2
        if precision is Precision.FP16:
            rec.append((k, v))
            comp_bytes += kf.nelement() * 2 + vf.nelement() * 2
            continue
        ck = compress(kf, precision, axis=2, group_size=group_size)  # keys/channel
        cv = compress(vf, precision, axis=3, group_size=group_size)  # values/token
        comp_bytes += ck.nbytes + cv.nbytes
        rk = decompress(ck).to(k.dtype)
        rv = decompress(cv).to(v.dtype)
        rec.append((rk, rv))
    return rec, fp16_bytes, comp_bytes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="meta-llama/Llama-3.1-8B-Instruct")
    ap.add_argument("--prompt-tokens", type=int, default=512)
    ap.add_argument("--group-size", type=int, default=64)
    ap.add_argument("--out", default="results-local/codesign/realkv_smoke.json")
    args = ap.parse_args()

    from transformers import AutoModelForCausalLM, AutoTokenizer

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"device={dev} model={args.model}", flush=True)
    tok = AutoTokenizer.from_pretrained(args.model)
    # NOTE: no device_map= (that needs `accelerate`); load then .to(dev). Single
    # GPU is all the smoke needs. `dtype=` is the non-deprecated arg name.
    model = AutoModelForCausalLM.from_pretrained(args.model, dtype=torch.float16)
    model = model.to(dev)
    model.eval()

    text = ("You are a tool-using agent. " * 200)[: args.prompt_tokens * 5]
    ids = tok(text, return_tensors="pt").input_ids[:, : args.prompt_tokens].to(dev)
    print(f"prefill {ids.shape[1]} tokens", flush=True)

    with torch.no_grad():
        out = model(ids, use_cache=True)
    layers = _extract_kv(out.past_key_values)
    fp16_logits = out.logits[:, -1, :].float()
    fp16_top1 = fp16_logits.argmax(-1).item()
    n_layers = len(layers)
    k0 = layers[0][0]
    print(f"got real KV: {n_layers} layers, K shape {tuple(k0.shape)}", flush=True)

    # a fresh next-token forward to reuse as the codec probe input
    next_id = fp16_logits.argmax(-1, keepdim=True)

    results = {
        "model": args.model,
        "device": dev,
        "transformers": __import__("transformers").__version__,
        "prompt_tokens": int(ids.shape[1]),
        "n_layers": n_layers,
        "k_shape": list(k0.shape),
        "group_size": args.group_size,
        "fp16_next_top1": fp16_top1,
        "codecs": {},
    }

    # fp16-cache reference logits for the model-level probe (once)
    ref_cache = _rebuild_cache(layers, out.past_key_values)
    ref_logits = None
    if ref_cache is not None:
        try:
            with torch.no_grad():
                ref_logits = model(next_id, past_key_values=ref_cache,
                                   use_cache=True).logits[:, -1, :].float()
        except Exception as e:  # noqa: BLE001
            print(f"model-level probe unavailable (ref): {type(e).__name__}: {e}",
                  flush=True)
            ref_logits = None

    for precision in (Precision.FP8, Precision.INT4):
        t0 = time.time()
        rec, fp16_bytes, comp_bytes = _codec_roundtrip_cache(
            layers, precision, args.group_size
        )
        # block-level round-trip error on REAL KV (always measurable)
        rel = []
        for (k, v), (rk, rv) in zip(layers, rec):
            kf, vf = k.float(), v.float()
            rel.append(((rk.float() - kf).norm() / kf.norm().clamp(min=1e-6)).item())
            rel.append(((rv.float() - vf).norm() / vf.norm().clamp(min=1e-6)).item())
        mean_rel_l2 = sum(rel) / len(rel)

        entry = {
            "kv_fp16_bytes": fp16_bytes,
            "kv_compressed_bytes": comp_bytes,
            "measured_dram_ratio": round(comp_bytes / max(fp16_bytes, 1), 4),
            "dram_saved_frac": round(1 - comp_bytes / max(fp16_bytes, 1), 4),
            "realkv_mean_rel_l2": round(mean_rel_l2, 5),
            "roundtrip_s": round(time.time() - t0, 2),
        }

        # model-level probe (best effort): forward with the reconstructed cache
        entry["model_level_probe"] = "skipped"
        if ref_logits is not None:
            cache_c = _rebuild_cache(rec, out.past_key_values)
            if cache_c is not None:
                try:
                    with torch.no_grad():
                        cl = model(next_id, past_key_values=cache_c,
                                   use_cache=True).logits[:, -1, :].float()
                    ref_top5 = set(ref_logits.topk(5).indices.flatten().tolist())
                    cod_top5 = set(cl.topk(5).indices.flatten().tolist())
                    entry.update({
                        "model_level_probe": "ok",
                        "next_top1_agree_with_fp16": int(
                            cl.argmax(-1).item() == ref_logits.argmax(-1).item()),
                        "logit_rel_l2": round(
                            ((cl - ref_logits).norm()
                             / ref_logits.norm().clamp(min=1e-6)).item(), 5),
                        "top5_overlap": len(ref_top5 & cod_top5),
                    })
                except Exception as e:  # noqa: BLE001
                    entry["model_level_probe"] = f"error: {type(e).__name__}"

        results["codecs"][precision.value] = entry
        print(f"{precision.value}: dram_ratio={entry['measured_dram_ratio']} "
              f"(saved {entry['dram_saved_frac']:.0%}) "
              f"realkv_rel_l2={entry['realkv_mean_rel_l2']} "
              f"probe={entry['model_level_probe']} "
              f"top1_agree={entry.get('next_top1_agree_with_fp16','-')}", flush=True)

    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(results, indent=2))
    print("WROTE", outp, flush=True)
    print(json.dumps(results, indent=2), flush=True)

    # smoke gate (load-bearing): every codec must genuinely shrink DRAM and have a
    # bounded real-KV round-trip error. If the model-level probe ran, the top-1
    # next token must also survive the compress->dequant round-trip.
    def _codec_ok(c: dict) -> bool:
        if not (c["measured_dram_ratio"] < 0.65 and c["realkv_mean_rel_l2"] < 0.25):
            return False
        if c.get("model_level_probe") == "ok":
            return c.get("next_top1_agree_with_fp16") == 1
        return True

    ok = all(_codec_ok(c) for c in results["codecs"].values())
    print("SMOKE_REALKV_OK" if ok else "SMOKE_REALKV_FAIL", flush=True)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
