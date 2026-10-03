"""In-memory synthetic receipt tests; no simulated paper results are generated."""
import copy,json
from pathlib import Path
from ma_metadata import complete,implemented_complete,original_scope_available,fingerprint,implementation_fingerprint,bank_complete


class Input:
    def __init__(self,name,data):self.name,self.data=name,data
    def read_bytes(self):return self.data


class Bank:
    def __init__(self,data):self.data=data
    def glob(self,pattern):return [Input(k,v) for k,v in self.data.items()]
    def __truediv__(self,name):return Input(name,self.data[name])


def run():
    c=json.loads(Path(__file__).with_name("full_config.json").read_text());fp=fingerprint(b"config",b"job")
    flags=["mrt_converged","zf_converged","mrt_nominal_design_spacing_feasible","zf_nominal_design_spacing_feasible","mrt_nominal_design_box_feasible","zf_nominal_design_box_feasible"]
    # Zeros are synthetic status-test scaffolding, never written as curves.
    receipt={"input_fingerprint":fp,"implementation_fingerprint":implementation_fingerprint(),"checks":{k:True for k in flags},"metrics":{"schemes":{k:{"sample_sum_rates":[0.]*c["nlos_realizations_per_geometry"],"nonconverged_samples":0} for k in ["MA-MRT","MA-ZF","FPA-MRT","FPA-ZF","FPA-OPT"]}}}
    assert complete(receipt,fp,{},c)
    assert not complete(receipt,fingerprint(b"changed config",b"job"),{},c)
    assert not complete(receipt,fingerprint(b"config",b"changed job"),{},c)
    stale=copy.deepcopy(receipt);stale["implementation_fingerprint"]="old engine";assert not complete(stale,fp,{},c)
    failed=copy.deepcopy(receipt);failed["status"]="failed";assert not complete(failed,fp,{},c)
    nonconverged=copy.deepcopy(receipt);nonconverged["checks"]["zf_converged"]=False;assert not complete(nonconverged,fp,{},c)
    short=copy.deepcopy(receipt);short["metrics"]["schemes"]["MA-MRT"]["sample_sum_rates"].pop();assert not complete(short,fp,{},c)
    brute=copy.deepcopy(receipt);brute["metrics"]["brute_force"]={"MRT":{"search":{"complete":True}},"ZF":{"search":{"complete":False}}}
    assert not complete(brute,fp,{"brute_force_D":3},c)
    brute["metrics"]["brute_force"]["ZF"]["search"]["complete"]=True;assert complete(brute,fp,{"brute_force_D":3},c)
    correlated=copy.deepcopy(receipt);correlated["metrics"]["correlated_extension"]={k:{"sample_sum_rates":[0.]*c["nlos_realizations_per_geometry"]} for k in ["MA-MRT_MC","MA-ZF_MC"]}
    correlated["metrics"]["correlated_extension"]["ZF_Eq75_status"]="blocked_by_Eq72_74_dimension_mismatch"
    assert implemented_complete(correlated,fp,{"correlated":True},c)
    assert not original_scope_available({"correlated":True})
    assert not complete(correlated,fp,{"correlated":True},c)
    assert complete(correlated,fp,{"correlated":False},c)
    correlated["history"]={"mrt":{"objective":[0.,0.],"instantaneous_MC_mean":[0.,0.]},
                           "zf":{"objective":[0.,0.],"instantaneous_MC_mean":[0.,0.]}}
    for key in ["MRT_correlated_MC_history","MRT_Eq69_history","ZF_correlated_MC_history"]:
        correlated["metrics"]["correlated_extension"][key]=[0.,0.]
    for figure in [13,15]:
        assert original_scope_available({"correlated":True,"figure":figure})
        assert complete(correlated,fp,{"correlated":True,"figure":figure},c)
    for figure in [14,16]:
        assert not original_scope_available({"correlated":True,"figure":figure})
        assert implemented_complete(correlated,fp,{"correlated":True,"figure":figure},c)
        assert not complete(correlated,fp,{"correlated":True,"figure":figure},c)
    missing_curve=copy.deepcopy(correlated);missing_curve["metrics"]["correlated_extension"].pop("MRT_Eq69_history")
    assert not complete(missing_curve,fp,{"correlated":True,"figure":13},c)
    bad_curve=copy.deepcopy(correlated);bad_curve["history"]["mrt"]["instantaneous_MC_mean"][0]=float("nan")
    assert not complete(bad_curve,fp,{"correlated":True,"figure":15},c)
    assert not complete(receipt,fp,{"figure":3},c)
    correlated["metrics"]["correlated_extension"]["MA-ZF_MC"]["sample_sum_rates"][0]=float("inf")
    assert not implemented_complete(correlated,fp,{"correlated":True},c)
    data={f"case-000-mc-{r:03d}.json":f"synthetic input identity {r}".encode() for r in range(100)}
    manifest={"case_count":1,"realizations_per_case":100,"files":[{"filename":k,"case_index":0,"realization":r,"input_fingerprint":fingerprint(b"config",v)} for r,(k,v) in enumerate(data.items())]}
    assert bank_complete(Bank(data),manifest,b"config")
    missing=dict(data);missing.pop(next(iter(missing)));assert not bank_complete(Bank(missing),manifest,b"config")
    changed=dict(data);changed[next(iter(changed))]=b"changed input";assert not bank_complete(Bank(changed),manifest,b"config")
    duplicate=copy.deepcopy(manifest);duplicate["files"][-1]["realization"]=0;assert not bank_complete(Bank(data),duplicate,b"config")
    print("MA metadata tests passed: stale/failed/incomplete receipts never resume; MRT13/15 support model-comparison scope with all histories, ZF14/16 remain blocked; missing/nonfinite actual histories fail.")


if __name__=="__main__":run()
