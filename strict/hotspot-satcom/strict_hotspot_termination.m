function out=strict_hotspot_termination(action,varargin)
% Receipt-only success gates; no optimization/model operations are modified.
switch action
    case 'relative'
        h=varargin{1};cap=varargin{2};tol=varargin{3};residual=[];
        if numel(h)>=2,residual=(h(end)-h(end-1))/max(abs(h(end-1)),1e-12);end
        done=~isempty(residual)&&isfinite(residual)&&isfinite(tol)&&tol>0&&residual<tol;reason='configured_iteration_cap';if done,reason='relative_improvement';end
        out=struct('converged',done,'termination',reason,'iterations',numel(h)-1,'iteration_cap',cap,'stop_rule','signed_relative_objective_increase','threshold',tol,'final_residual',residual);
    case 'gradient'
        value=varargin{1};iterations=varargin{2};cap=varargin{3};tol=varargin{4};done=isfinite(value)&&isfinite(tol)&&tol>0&&value<=tol;reason='configured_iteration_cap';if done,reason='gradient_tolerance';end
        out=struct('converged',done,'termination',reason,'iterations',iterations,'iteration_cap',cap,'stop_rule','Riemannian_gradient_norm','threshold',tol,'final_residual',value);
    case 'scheme'
        stops=varargin{1};records=varargin{2};settings=varargin{3};flat={};
        for k=1:numel(records)
            r=records{k};if isfield(r,'active'),flat=[flat,{r.active,r.phase}];else,flat{end+1}=r;end %#ok<AGROW>
        end
        primal=0;bound=0;primalValid=~isempty(flat);boundValid=~isempty(flat);
        for k=1:numel(flat)
            r=flat{k};valid=isfield(r,'constraint_max_relative_violation');
            if valid,v=r.constraint_max_relative_violation;valid=isscalar(v)&&isfinite(v)&&v>=0;if valid,primal=max(primal,v);end,end
            primalValid=primalValid&&valid;valid=false;
            if isfield(r,'qt_bound_max_violation'),v=r.qt_bound_max_violation;valid=true;elseif isfield(r,'sdr_bound_max_violation'),v=r.sdr_bound_max_violation;valid=true;end
            if valid,valid=isscalar(v)&&isfinite(v)&&v>=0;if valid,bound=max(bound,v);end,end
            boundValid=boundValid&&valid;
        end
        ptol=1e-5;btol=1e-5;if isfield(settings,'solver_primal_relative_tolerance'),ptol=settings.solver_primal_relative_tolerance;end;if isfield(settings,'qt_bound_tolerance'),btol=settings.qt_bound_tolerance;end
        numerical=struct('solver_primal_pass',primalValid&&isfinite(ptol)&&ptol>0&&primal<=ptol,'qt_sdr_bound_pass',boundValid&&isfinite(btol)&&btol>0&&bound<=btol,'solver_primal_relative_tolerance',ptol,'qt_bound_tolerance',btol,'maximum_primal_relative_violation',primal,'maximum_qt_sdr_bound_violation',bound);
        done=~isempty(stops)&&all(cellfun(@stop_valid,stops));reason='one_or_more_configured_caps';if done,reason='all_original_stop_rules_reached';end
        out=struct('converged',done,'termination',reason,'blocks',{stops},'numerical',numerical,'algorithm_success',done&&numerical.solver_primal_pass&&numerical.qt_sdr_bound_pass);
    otherwise,error('Unknown termination receipt action');
end
end

function valid=stop_valid(s)
valid=isfield(s,'converged')&&isequal(s.converged,true)&&isfield(s,'final_residual')&&isfield(s,'threshold')&&isfield(s,'stop_rule');if ~valid,return;end
v=s.final_residual;t=s.threshold;valid=isscalar(v)&&isfinite(v)&&isscalar(t)&&isfinite(t)&&t>0&&any(strcmp(s.stop_rule,{'signed_relative_objective_increase','Riemannian_gradient_norm'}));
if valid,if strcmp(s.stop_rule,'Riemannian_gradient_norm'),valid=v<=t;else,valid=v<t;end,end
end
