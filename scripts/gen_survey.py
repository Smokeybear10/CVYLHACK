"""Run the team's Stage 2 survey swarm (stub/offline) over the frontend's
finalists and emit demo/mockups/survey.js (window.SURVEY keyed by site id)."""
import json, re
from pathlib import Path
from survey.bundler import bundles_from_contract
from survey.orchestrator import run_survey, reports_only
from survey.client import StubClient

ROOT = Path(__file__).resolve().parent.parent
raw = (ROOT/"demo/mockups/data.js").read_text()
mock = json.loads(re.sub(r"^window\.MOCK=", "", raw).rstrip().rstrip(";"))
sites = sorted(mock["sites"], key=lambda s: -s["score"])[:60]   # survey the finalists

def band(c): return "low" if c<=12000 else ("high" if c>=30000 else "moderate")
def verdict(s): 
    if s.get("gate"): return "No-go"
    return "Go" if s["score"]>=70 else ("Conditional" if s["score"]>=45 else "No-go")

feats=[]
for s in sites:
    m=s["m"]; f=s["f"]
    feats.append({"type":"Feature","geometry":{"type":"LineString","coordinates":s["g"]},
      "properties":{
        "cand_id":s["id"],"address_st":s["addr"],"score":s["score"],"verdict":verdict(s),
        "gated":bool(s.get("gate")),"gate_reasons":[s["gate"]] if s.get("gate") else [],
        "components":{"power":f["power"],"demand":f["demand"],"fit":f["mounting"],
                      "pavement":round(m["pci"]/100,3),"obstruction":max(0.0,1-m["n_obst"]/4)},
        "pci":m["pci"],"label":m["pci_label"],"length_ft":m["frontage_ft"],
        "road_width_ft":m["width_ft"],"dist_to_power_m":m["dist_power"],
        "obstruction_count":m["n_obst"],"disqualify_marking":bool(m["fire"]),
        "functional_class":5.0,"residential_suit":0.8,"traffic_suit":0.6,
        "est_make_ready_usd":float(s["cost"]),"connection_cost_band":band(s["cost"])}})

contract={"region":mock["meta"]["bounds"],"sites":feats}
bundles=bundles_from_contract(contract)
reports=reports_only(run_survey(bundles, StubClient(), use_cache=False))
out={r.site.id:r.model_dump() for r in reports}
(ROOT/"demo/mockups/survey.js").write_text("window.SURVEY="+json.dumps(out)+";")
tiers={}
for r in reports: tiers[r.verdict.tier]=tiers.get(r.verdict.tier,0)+1
print(f"surveyed {len(reports)} finalists -> demo/mockups/survey.js ({(ROOT/'demo/mockups/survey.js').stat().st_size//1024} KB)")
print("tiers:",tiers)
print("sample:",reports[0].site.id,reports[0].verdict.tier,"|",reports[0].verdict.one_line_reason)
