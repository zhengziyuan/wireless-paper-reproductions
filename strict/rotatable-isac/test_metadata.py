"""In-memory synthetic receipt tests; no stored/hardcoded paper curves."""
import copy
from isac_metadata import complete,inner_complete,fingerprint,implementation_fingerprint,bank_complete


class Input:
    def __init__(self,name,data):self.name,self.data=name,data
    def read_bytes(self):return self.data


class Bank:
    def __init__(self,data):self.data=data
    def glob(self,pattern):return [Input(k,v) for k,v in self.data.items()]
    def __truediv__(self,name):return Input(name,self.data[name])


def run():
    fp=fingerprint(b"config",b"scene");names=["Rot-BS & Rot-RIS","Rot-BS & Fix-RIS","Fix-BS & Rot-RIS","Fix-BS & Fix-RIS","Rot-BS & No-RIS","Fix-BS & No-RIS"]
    common={"converged":True,"capped_unconverged":False,"iterations":1,"iteration_budget":500}
    block={"W":dict(common,termination_reason="relative_objective_tolerance",relative_objective_improvement=0.,relative_tolerance=1e-6),
           "RIS":dict(common,applicable=True,termination_reason="gradient_tolerance",last_checked_normalized_gradient_norm=0.,gradient_tolerance=1e-6),
           "rotation":dict(common,termination_reason="projected_gradient_tolerance",last_checked_projected_gradient_norm=0.,gradient_tolerance=1e-6)}
    receipt={"input_fingerprint":fp,"implementation_fingerprint":implementation_fingerprint(),"checks":{n:{"status":"executed","converged":True,"inner_all_converged":True,"full_converged":True,"power_feasible":True,"rotation_feasible":True,"unit_modulus_error":0.} for n in names},
             "metrics":{n:{"utility":0.,"rate":0.,"nmse":0.} for n in names},
             "history":{n:{"inner_all_converged":True,"full_converged":True,"blocks":[copy.deepcopy(block)]} for n in names}}
    assert complete(receipt,fp)
    assert not complete(receipt,fingerprint(b"different config",b"scene"))
    assert not complete(receipt,fingerprint(b"config",b"different scene"))
    stale=copy.deepcopy(receipt);stale["implementation_fingerprint"]="old engine";assert not complete(stale,fp)
    failed=copy.deepcopy(receipt);failed["checks"][names[4]]["status"]="failed";assert not complete(failed,fp)
    nonconverged=copy.deepcopy(receipt);nonconverged["checks"][names[0]]["converged"]=False;assert not complete(nonconverged,fp)
    partial=copy.deepcopy(receipt);del partial["checks"][names[-1]];assert not complete(partial,fp)
    for kind in ["W","RIS","rotation"]:
        capped=copy.deepcopy(receipt);item=capped["history"][names[0]]["blocks"][0][kind]
        item.update(converged=False,capped_unconverged=True,termination_reason="maximum_iterations_without_criterion_stop",iterations=500)
        assert not complete(capped,fp)  # Outer convergence cannot override any inner cap.
    inaccurate=copy.deepcopy(receipt);inaccurate["history"][names[0]]["blocks"][0]["RIS"]["last_checked_normalized_gradient_norm"]=1.
    assert not complete(inaccurate,fp)  # Even true summary flags cannot override actual unmet tolerance.
    missing=copy.deepcopy(receipt);del missing["history"];assert not complete(missing,fp)
    last=copy.deepcopy(block["W"]);last.update(iterations=500,budget_exhausted=True);assert inner_complete(last,"W")
    inactive={"applicable":False,"converged":True,"capped_unconverged":False,"termination_reason":"not_applicable_no_RIS","iterations":0}
    assert inner_complete(inactive,"RIS") and not inner_complete(inactive,"W")
    data={f"case-000-mc-{r:03d}.json":f"synthetic input identity {r}".encode() for r in range(100)}
    manifest={"case_count":1,"files":[{"filename":k,"case_index":0,"realization":r,"input_fingerprint":fingerprint(b"config",v)} for r,(k,v) in enumerate(data.items())]}
    assert bank_complete(Bank(data),manifest,b"config")
    missing=dict(data);missing.pop(next(iter(missing)));assert not bank_complete(Bank(missing),manifest,b"config")
    changed=dict(data);changed[next(iter(changed))]=b"changed input";assert not bank_complete(Bank(changed),manifest,b"config")
    duplicate=copy.deepcopy(manifest);duplicate["files"][-1]["realization"]=0;assert not bank_complete(Bank(data),duplicate,b"config")
    print("ISAC metadata tests passed: stale/failed/partial receipts and outer-converged but inner-capped or unmet-criterion outcomes never resume.")


if __name__=="__main__":run()
