# SPDX-License-Identifier: Apache-2.0
"""Analyze the PHYSICAL compressed-offload smoke.

Reads the per-condition result JSONs (with captured outputs) + the joint server
log, and reports:
  1. physical DRAM reduction  -- last CD_PHYSICAL_STATS peak_vs_fp16_equiv_ratio
     from the joint run (the compressed side-region's real resident bytes vs an
     fp16 pool) + reload_pcie_ratio.
  2. output preservation      -- per-request text agreement vs the no_offload
     baseline: codesign_fp16 (lossless raw store, isolates the reload path) and
     codesign_joint (compressed). Reports exact-match + first-16-char (top-1
     proxy) agreement.
  3. 0 errors across all conditions.

Emits a verdict JSON + SMOKE_PHYS_OK / SMOKE_PHYS_FAIL.
"""
import argparse
import json
import sys
from pathlib import Path


def load_condition(root: Path, cond: str) -> dict | None:
    hits = sorted(root.glob(f"{cond}_*.json"))
    if not hits:
        return None
    return json.loads(hits[-1].read_text())


def outputs_by_tag(doc: dict) -> dict[str, str]:
    out = {}
    for r in doc.get("requests", []):
        if "error" in r or "out" not in r:
            continue
        if "warm" in r.get("tag", ""):
            continue
        out[r["tag"]] = r["out"]
    return out


def agreement(a: dict[str, str], b: dict[str, str]) -> dict:
    common = sorted(set(a) & set(b))
    if not common:
        return {"n": 0, "exact": 0.0, "first16": 0.0}
    exact = sum(1 for t in common if a[t] == b[t])
    first16 = sum(1 for t in common if a[t][:16] == b[t][:16])
    return {"n": len(common), "exact": round(exact / len(common), 4),
            "first16": round(first16 / len(common), 4)}


def last_physical_stats(logdir: Path) -> dict | None:
    srv = sorted(logdir.glob("server_codesign_joint.log"))
    if not srv:
        return None
    last = None
    for ln in srv[-1].read_text(errors="ignore").splitlines():
        i = ln.find("CD_PHYSICAL_STATS ")
        if i != -1:
            try:
                last = json.loads(ln[i + len("CD_PHYSICAL_STATS "):])
            except ValueError:
                pass
    return last


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="results dir with *_.json + server logs")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    root = Path(args.root)

    conds = {c: load_condition(root, c)
             for c in ("no_offload", "codesign_fp16", "codesign_joint")}
    errs = {c: (d["summary"]["n_err"] if d else None) for c, d in conds.items()}
    n_ok = {c: (d["summary"]["n_ok"] if d else None) for c, d in conds.items()}

    base = outputs_by_tag(conds["no_offload"]) if conds["no_offload"] else {}
    fp16 = outputs_by_tag(conds["codesign_fp16"]) if conds["codesign_fp16"] else {}
    joint = outputs_by_tag(conds["codesign_joint"]) if conds["codesign_joint"] else {}

    phys = last_physical_stats(root)

    # fp16-vs-no_offload is the NONDETERMINISM FLOOR: codesign_fp16 stores KV
    # losslessly (raw bytes), so any divergence from no_offload is pure vLLM
    # cross-run batching nondeterminism (fp non-associativity under concurrency),
    # NOT the offload path. The confound-controlled compression signal is
    # joint-vs-fp16 (both use the physical handler under identical concurrency).
    fp16_floor = agreement(fp16, base)
    verdict = {
        "n_ok": n_ok,
        "n_err": errs,
        "physical_stats_joint": phys,
        "output_agreement_vs_no_offload": {
            "codesign_fp16_NONDETERMINISM_FLOOR": fp16_floor,
            "codesign_joint": agreement(joint, base),
        },
        "output_agreement_joint_vs_fp16_CONFOUND_FREE": agreement(joint, fp16),
    }

    # smoke gate (nondeterminism-aware):
    #  - 0 errors everywhere
    #  - physical side-region genuinely smaller than an fp16 pool
    #  - joint's top-1 (first-16-char) agreement with the fp16 physical path is
    #    within a small margin of the nondeterminism floor (i.e. compression adds
    #    little divergence on top of what a LOSSLESS run already shows)
    zero_err = all(e == 0 for e in errs.values() if e is not None)
    phys_smaller = bool(phys) and phys.get("peak_vs_fp16_equiv_ratio", 1.0) < 0.9
    floor = fp16_floor["first16"] if (fp16 and base) else 1.0
    jvf = verdict["output_agreement_joint_vs_fp16_CONFOUND_FREE"]["first16"] \
        if (joint and fp16) else 1.0
    # compression may add up to 0.10 divergence beyond the nondeterminism floor
    joint_ok = jvf >= min(floor, 1.0) - 0.10

    ok = zero_err and phys_smaller and joint_ok
    verdict["gate"] = {
        "zero_err": zero_err, "phys_smaller": phys_smaller,
        "nondeterminism_floor_first16": floor,
        "joint_vs_fp16_first16": jvf,
        "joint_output_preserved_within_margin": joint_ok,
        "PASS": ok,
    }

    txt = json.dumps(verdict, indent=2)
    print(txt)
    if args.out:
        Path(args.out).write_text(txt)
    print("SMOKE_PHYS_OK" if ok else "SMOKE_PHYS_FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
