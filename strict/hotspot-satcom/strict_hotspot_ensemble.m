function varargout=strict_hotspot_ensemble(action,varargin)
% Declared initialization only; no changed optimizer, QoS or model.
switch action
    case 'phases',varargout={phases(varargin{:})};
    case 'initialize',[varargout{1:nargout}]=initialize(varargin{:});
    case 'summarize',[varargout{1:nargout}]=summarize(varargin{:});
    otherwise,error('Unknown ensemble action');
end
end

function schedule=phases(phi0,seed,U)
schedule=cell(1,U+1);schedule{1}=phi0(:);
for start=1:U
    uniform=zeros(numel(phi0),1);
    for m=0:numel(phi0)-1
        text=sprintf('%d:3309957:%d:100000:%d:%d',seed,U,start,m);
        md=java.security.MessageDigest.getInstance('SHA-256');md.update(uint8(text));raw=typecast(md.digest(),'uint8');hex=lower(reshape(dec2hex(raw,2).',1,[]));
        uniform(m+1)=hex2dec(hex(1:13))/2^52;
    end
    schedule{start+1}=exp(2i*pi*uniform);
end
end

function [W,proof]=initialize(Q,Psi,W0,noise,power,target,startID)
U=size(Q,1);K=size(Psi,1);W=W0;target=target(:);
assert(startID>=0&&startID<=U&&startID==floor(startID));
proof=struct('start_id',startID,'selected_HU',[],'same_original_constraints',true);
if startID>0
    user=startID;direction=W(:,user);assert(norm(direction)>0);direction=direction/norm(direction);W(:,1:U)=0;
    allowance=zeros(K,1);coupling=zeros(K,1);
    for k=1:K
        pk=squeeze(Psi(k,:,:));received=real(sum(conj(W).*(pk*W),1));desired=received(U+k);
        allowance(k)=desired/target(k)-(sum(received)-desired+noise);coupling(k)=real(direction'*pk*direction);
    end
    assert(min(allowance)>=-1e-10&&min(coupling)>=-1e-10,'Original fixed NHU beams or moments invalid');
    available=max(0,power-sum(abs(W(:)).^2));limits=Inf(K,1);positive=coupling>0;limits(positive)=max(allowance(positive),0)./coupling(positive);
    allocated=min(available,min(limits));W(:,user)=sqrt(allocated)*direction;
    proof.selected_HU=startID-1;proof.HU_power=allocated;proof.NHU_slack_before_restoring_HU=allowance;proof.coupling=coupling;
end
e=strict_hotspot_statistical('evaluate',Q,Psi,W,noise);proof.evaluation=e;
proof.physical_feasibility_pass=e.total_power<=power*(1+1e-5)&&min(e.sinr(U+1:end)-target)>=-1e-5;
assert(proof.physical_feasibility_pass,'Declared start violates original constraints');
end

function [summary,selected]=summarize(records,required)
gates={'physical_constraint_pass','convergence_pass','solver_primal_pass','qt_sdr_bound_pass'};
ids=cellfun(@(r)r.start_id,records);required=required(:).';allExecuted=numel(ids)==numel(required)&&isequal(sort(ids),sort(required))&&all(cellfun(@(r)isfield(r,'executed')&&r.executed,records));
checks=struct();for k=1:numel(gates),checks.(gates{k})=allExecuted&&all(cellfun(@(r)r.checks.(gates{k}),records));end
best=-Inf;selected=[];
for k=1:numel(records)
    r=records{k};good=r.executed&&all(cellfun(@(g)r.checks.(g),gates));
    if good&&(r.evaluation.hu_sum_rate>best||(r.evaluation.hu_sum_rate==best&&r.start_id<selected.start_id)),selected=r;best=r.evaluation.hu_sum_rate;end
end
id=[];if ~isempty(selected),id=selected.start_id;end
summary=struct('required_start_ids',required,'executed_start_ids',ids,'all_required_starts_executed',allExecuted, ...
    'all_required_starts_pass',all(structfun(@(x)x,checks)),'checks',checks,'selected_start_id',id, ...
    'selection_rule','maximum original source approximate sum-rate among completed physically feasible trajectories; lowest start ID breaks exact ties', ...
    'selection_does_not_certify_failed_or_capped_ensemble',true);
end
