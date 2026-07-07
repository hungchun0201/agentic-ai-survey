import json, glob, random, statistics as st
random.seed(0)
def p95(xs): xs=sorted(xs); return xs[max(0,int(0.95*len(xs))-1)]
def boot(all_lat, n=2000):
    vs=[]
    for _ in range(n):
        s=[random.choice(all_lat) for _ in range(len(all_lat))]
        vs.append(p95(s))
    vs.sort(); return vs[int(0.025*n)], vs[int(0.975*n)]
for sku in ["h100","a100-80"]:
    for cond in ["codesign_fp16","codesign_joint"]:
        for dram in ["dram4","dram8"]:
            pooled=[]; jcts=[]; nseed=0
            for d in sorted(glob.glob(f"results-m1swe/m1swe_{sku}_{cond}_jps0.5_{dram}_seed*")):
                js=glob.glob(d+"/*.json")
                if not js: continue
                j=json.load(open(js[0])); nseed+=1
                for t in j.get("requests", []):
                    x=t.get("total_s")
                    if x is not None: pooled.append(x)
                jcts.extend(job["jct_s"] for job in j.get("jobs",[]) if job.get("jct_s") is not None)
            if not pooled: continue
            lo,hi=boot(pooled)
            print(f"{sku} {cond} {dram}: seeds={nseed} turns={len(pooled)} p95={p95(pooled):.2f} [{lo:.2f},{hi:.2f}] mean={st.mean(pooled):.2f} meanJCT={st.mean(jcts):.1f}")
