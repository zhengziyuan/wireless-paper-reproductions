function value=ma6_passive_capture_v1(stage,data)
% Observer only. Record actual already-computed locals; never evaluate a model.
persistent records errors
if strcmp(stage,'initialize'),records={};errors={};value=[];return;end
if strcmp(stage,'finish'),value=struct('records',{records},'observer_errors',{errors},'no_extra_model_or_solver_evaluation',true);return;end
try
    records{end+1}=struct('stage',stage,'actual_locals',data);
catch problem
    errors{end+1}=struct('stage',stage,'identifier',problem.identifier,'message',problem.message);
end
value=[];
end
