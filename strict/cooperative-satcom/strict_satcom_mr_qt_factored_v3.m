function [out,info,state]=strict_satcom_mr_qt_factored_v3(p0,signal,cross,power,leak,offset,powerLimit,interferenceLimit)
% Prospective v3: exact sqrt(scale*v) factorization, same original MR QT/duals/gates.
[J,U]=size(p0);K=size(leak,3);
before=strict_satcom_core('mr_evaluate',p0,signal,cross,power,leak,offset);
y=sqrt(max(p0.*signal,0))./before.denominator.';B=cross;
for u=1:U,B(:,u,u)=B(:,u,u)-signal(:,u);end
assert(min(B(:))>=-1e-9);B=max(B,0);
scale=powerLimit(:)./max(power,1e-300);
for k=1:K,scale=min(scale,interferenceLimit(k)./max(leak(:,:,k),1e-300));end
objectiveScale=max(1e-6,max(sum(scale.*signal,1).'./offset(:)));
try
cvx_begin quiet
    variable scaledPower(J,U) nonnegative
    expression p(J,U)
    p=scale.*scaledPower;
    variable minSinr
    dual variables userDual{U} powerDual{J} leakageDual{K}
    maximize(minSinr)
    subject to
    for u=1:U
        denom=offset(u)+sum(sum(reshape(B(:,u,:),J,U).*p));
        userDual{u} : minSinr<=(sum(2*y(:,u).*sqrt(signal(:,u).*scale(:,u)).*sqrt(scaledPower(:,u)))-sum(y(:,u).^2)*denom)/objectiveScale;
    end
    for j=1:J,powerDual{j} : sum((power(j,:)/powerLimit(j)).*p(j,:))<=1;end
    for k=1:K,leakageDual{k} : sum(sum((leak(:,:,k)/interferenceLimit(k)).*p))<=1;end
cvx_end
catch constructionException
    % A model-construction exception must clear CVX in its owning workspace.
    % This error-only boundary does not change a solved subproblem or retry gate.
    cvx_clear;
    rethrow(constructionException);
end
assert(contains(cvx_status,'Solved'),'Original MR QT solver failed: %s',cvx_status);
out=max(scale.*scaledPower,0);after=strict_satcom_core('mr_evaluate',out,signal,cross,power,leak,offset);
qt=sum(2*y.*sqrt(p0.*signal),1).'-sum(y.^2,1).'.*before.denominator;
newqt=sum(2*y.*sqrt(out.*signal),1).'-sum(y.^2,1).'.*after.denominator;
primal=max([0;-scaledPower(:);minSinr-newqt/objectiveScale;after.satellite_power./powerLimit(:)-1;after.gt_interference./interferenceLimit(:)-1]);
info=struct('solver_status',cvx_status,'surrogate_minimum_sinr',minSinr*objectiveScale, ...
    'solver_diagnostics',struct('solver','external_CVX','status',cvx_status,'reported_solver_tolerance',cvx_slvtol,'constraint_max_relative_violation',primal), ...
    'qt_bound_max_violation',max(0,minSinr*objectiveScale-min(after.sinr)), ...
    'qt_tightness_error',max(abs(qt-before.sinr)),'before',before,'after',after);
alpha=real(cellfun(@(x)x,userDual));rho=real(cellfun(@(x)x,powerDual));nu=real(cellfun(@(x)x,leakageDual));
alpha=alpha(:);rho=rho(:);nu=nu(:);kappa=sum(y.^2,1).';
H=zeros(J,U);c=zeros(J,U);
for j=1:J,for v=1:U
    H(j,v)=rho(j)*power(j,v)/powerLimit(j);
    for k=1:K,H(j,v)=H(j,v)+nu(k)*leak(j,v,k)/interferenceLimit(k);end
    for u=1:U,H(j,v)=H(j,v)+alpha(u)*kappa(u)*B(j,u,v)/objectiveScale;end
    c(j,v)=alpha(v)*y(j,v)*sqrt(signal(j,v))/objectiveScale;
end,end
if all(H(:)>0),quadraticTerm=sum(sum(c.^2./H));else,quadraticTerm=inf;end
rawDual=(sum(rho)+sum(nu)-dot(alpha,kappa.*offset(:))/objectiveScale+quadraticTerm)*objectiveScale;
state=struct('actual_user_dual',alpha,'actual_power_dual',rho,'actual_leakage_dual',nu, ...
    'same_fixed_QT_auxiliary_y',y,'same_exact_coordinate_scale',scale,'same_objective_scale',objectiveScale, ...
    'actual_candidate',out,'actual_minimum_QT_value',minSinr*objectiveScale,'actual_new_QT_user_values',newqt, ...
    'raw_dual_sum_to_one_error',abs(sum(alpha)-1),'raw_dual_minimum_nonnegative_entry',min([alpha;rho;nu]), ...
    'raw_dual_quadratic_H_smallest_eigenvalue',min(H(:)), ...
    'raw_stationarity_max_residual',max(abs(H(:).*sqrt(out(:))-c(:))), ...
    'raw_dual_objective_NOT_certified_until_PSD_and_equality_recheck',rawDual, ...
    'raw_primal_dual_gap_NOT_certified',rawDual-minSinr*objectiveScale,'H',H,'c',c, ...
    'no_dual_certificate_claimed',true);
end
