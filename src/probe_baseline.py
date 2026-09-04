"""Baselines for the probe. A direction that separates arms is only interesting
if a random direction, and a shuffled-label fit, do not."""
import json, re
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

U="/mnt/user-data/uploads/Potato/quiet-motive/data/"
BARE=re.compile(r"\b(scor(e|es|ed|ing)|metric|measured|incentiv\w*|rewarded|graded|my performance|performance is)\b",re.I)
traj={r["traj_id"]:r for r in (json.loads(l) for l in open(U+"trajectories.jsonl",encoding="utf-8"))}
d=np.load(U+"activations.npz",allow_pickle=True)
X,layers=d["X"],list(d["layers"]); meta=json.loads(str(d["meta"]))
arm=np.array([m["arm"] for m in meta]); sid=np.array([m["scenario_id"] for m in meta])
tid=np.array([m["traj_id"] for m in meta])
quiet=np.array([not BARE.search(traj[t].get("reasoning") or "") for t in tid])
s1,s2="log_delete","test_edit"
li=layers.index(12); F=X[:,li,:]
tr=(sid==s1)&np.isin(arm,["A","B"]); te=(sid==s2)&np.isin(arm,["A","B"])
dq=(sid==s2)&(arm=="D")&quiet
ytr=(arm[tr]=="A").astype(int); yte=(arm[te]=="A").astype(int)

def fit(Xtr,y,seed=0):
    c=make_pipeline(StandardScaler(),LogisticRegression(max_iter=2000,C=0.1,random_state=seed))
    c.fit(Xtr,y); return c

print("Layer 12. Trained on log_delete arm A vs arm B, evaluated on test_edit.\n")
print(f"{'':<34} {'cross-scen A/B':>15} {'quiet D as A':>14}")

real=fit(F[tr],ytr)
print(f"{'the probe':<34} {(real.predict(F[te])==yte).mean():>14.1%} "
      f"{real.predict(F[dq]).mean():>13.1%}")

# 1. shuffled labels: same features, same fit, labels permuted
rng=np.random.default_rng(0); accs=[]; ds=[]
for s in range(200):
    yp=rng.permutation(ytr)
    c=fit(F[tr],yp,seed=s)
    accs.append((c.predict(F[te])==yte).mean()); ds.append(c.predict(F[dq]).mean())
print(f"{'shuffled training labels':<34} {np.mean(accs):>14.1%} {np.mean(ds):>13.1%}"
      f"   (200 draws, cross-scen 95% range "
      f"{np.percentile(accs,2.5):.0%} to {np.percentile(accs,97.5):.0%})")

# 2. random direction through the same pipeline
sc=StandardScaler().fit(F[tr]); Z_te=sc.transform(F[te]); Z_dq=sc.transform(F[dq])
accs=[]; ds=[]
for s in range(200):
    r=np.random.default_rng(1000+s).normal(size=F.shape[1])
    thr=np.median(sc.transform(F[tr])@r)
    accs.append(((Z_te@r>thr).astype(int)==yte).mean()); ds.append((Z_dq@r>thr).mean())
print(f"{'random direction, median split':<34} {np.mean(accs):>14.1%} {np.mean(ds):>13.1%}"
      f"   (200 draws, 95% range {np.percentile(accs,2.5):.0%} to {np.percentile(accs,97.5):.0%})")

# 3. layer 0, already in the paper, as the embedding control
li0=layers.index(0); F0=X[:,li0,:]
c0=fit(F0[tr],ytr)
print(f"{'layer 0 (embeddings)':<34} {(c0.predict(F0[te])==yte).mean():>14.1%} "
      f"{c0.predict(F0[dq]).mean():>13.1%}")
print("\nA direction that separates the arms is only worth reporting if these do not.")
