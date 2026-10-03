function [winner,certificate]=ma_exact_coordinate(t,c,antenna,mode,gradient,curvature,base,G,q,objectiveBefore)
% Complete 2D active-set solve of ORIGINAL convex coordinate subproblem.
% The final concavity upper-gap certificate does not depend on solver status.
position=t(antenna,:)';lo=c.region_lower(:)-position;hi=c.region_upper(:)-position;
A=[-1 0;0 -1;1 0;0 1];b=[-lo;hi];
for other=1:size(t,1),if other~=antenna,d=position-t(other,:)';A(end+1,:)=-2*d';b(end+1)=d'*d-c.minimum_distance^2;end,end
norms=vecnorm(A,2,2);assert(~any(norms==0&b<0),'Original spacing polygon infeasible');keep=norms>0;A=A(keep,:)./norms(keep);b=b(keep)./norms(keep);
feasibilityTolerance=2e-12*max(1,max(abs(b)));vertices=zeros(0,2);
for i=1:size(A,1),for j=1:i-1,matrix=A([i j],:);if abs(det(matrix))<=1e-13,continue;end;x=matrix\b([i j]);
if max(A*x-b)<=feasibilityTolerance&&~any(vecnorm(vertices-x',2,2)<feasibilityTolerance),vertices(end+1,:)=x';end
end,end
assert(~isempty(vertices),'No vertices of bounded original feasible polygon');candidates=vertices;if max(-b)<=feasibilityTolerance,candidates(end+1,:)=[0 0];end
if strcmp(mode,'MRT')
gradient=gradient(:);assert(curvature>=0,'Nonconcave source MRT minorant');
if curvature>0,x=gradient/curvature;if max(A*x-b)<=feasibilityTolerance,candidates(end+1,:)=x';end,end
for index=1:size(A,1)
[p,v,left,right,valid]=edge(index);if ~valid,continue;end
if curvature>0,parameter=min(max(v'*(gradient/curvature-p),left),right);elseif gradient'*v>0,parameter=right;else,parameter=left;end
candidates(end+1,:)=(p+parameter*v)';
end
else
assert(strcmp(mode,'ZF')&&all(base>0)&&all(q>=0),'Source ZF domain/concavity invalid');base=base(:);q=q(:);x=zeros(2,1);
for iteration=1:c.convex_solver.options.interior_newton_iteration_budget
[value,g]=evaluate(x);r=base+G*x-q/2*(x'*x);vectors=G-q.*x';negativeHessian=(sum(q./r)*eye(2)+vectors'*((1./r.^2).*vectors))/log(2);
if norm(g)<c.convex_solver.options.interior_gradient_tolerance,break;end
[V,D]=eig(negativeHessian,'vector');positive=D>eps*max(1,max(D));if ~any(positive),break;end
step=V(:,positive)*((V(:,positive)'*g)./D(positive));slope=g'*step;if slope<=0,break;end
alpha=1;accepted=false;
for backtrack=1:120,trialValue=evaluate(x+alpha*step);if trialValue>=value+1e-4*alpha*slope||(slope<1e-14&&isfinite(trialValue)),accepted=true;break;end;alpha=alpha/2;end
if ~accepted,break;end;trial=x+alpha*step;if isequal(trial,x),break;end;x=trial;
end
if max(A*x-b)<=feasibilityTolerance&&isfinite(evaluate(x)),candidates(end+1,:)=x';end
for index=1:size(A,1)
[p,v,left,right,valid]=edge(index);if ~valid,continue;end
constants=base+G*p-q/2*(p'*p);linear=(G-q.*p')*v;
for user=1:numel(base)
if q(user)>0,center=linear(user)/q(user);radiusSquared=center^2+2*constants(user)/q(user);if radiusSquared<=0,left=1;right=0;break;end;radius=sqrt(radiusSquared);left=max(left,center-radius);right=min(right,center+radius);
elseif abs(linear(user))>0,boundary=-constants(user)/linear(user);if linear(user)>0,left=max(left,boundary);else,right=min(right,boundary);end
elseif constants(user)<=0,left=1;right=0;break;end
end
if left>right,continue;end
if isfinite(evaluate(p+left*v)),candidates(end+1,:)=(p+left*v)';end
if isfinite(evaluate(p+right*v)),candidates(end+1,:)=(p+right*v)';end
if right-left<=feasibilityTolerance,continue;end
L=finiteEndpoint(left,right,p,v);R=finiteEndpoint(right,left,p,v);if isempty(L)||isempty(R)||L>R,continue;end
dL=edgeDerivative(L,p,v);dR=edgeDerivative(R,p,v);
if dL<=0,parameter=L;elseif dR>=0,parameter=R;else
% Monotone scalar derivative; bisection preserves the global edge bracket.
for iteration=1:200,middle=(L+R)/2;derivative=edgeDerivative(middle,p,v);if derivative>0,L=middle;else,R=middle;end;if R-L<=5e-15+1e-14*max(abs([L R])),break;end,end
parameter=(L+R)/2;
end
candidates(end+1,:)=(p+parameter*v)';
end
end
values=-Inf(size(candidates,1),1);for item=1:size(candidates,1),x=candidates(item,:)';if max(A*x-b)<=feasibilityTolerance,values(item)=evaluate(x);end,end
[maximum,index]=max(values);assert(isfinite(maximum),'No finite feasible original coordinate candidate');ties=find(values>=maximum-8*eps*max(1,abs(maximum)));bestGap=Inf;bestNorm=Inf;
for item=ties(:)',x=candidates(item,:)';[~,gradientValue]=evaluate(x);if ~all(isfinite(gradientValue)),continue;end;candidateGap=max(0,max((vertices-x')*gradientValue));candidateNorm=x'*x;
if candidateGap<bestGap||(candidateGap==bestGap&&candidateNorm<bestNorm),index=item;bestGap=candidateGap;bestNorm=candidateNorm;end,end
value=values(index);winner=candidates(index,:)';[~,g]=evaluate(winner);assert(all(isfinite(g)),'Finite original certificate gradient required');
gap=max(0,max((vertices-winner')*g));settings=c.convex_solver.options;gapTolerance=max(settings.objective_gap_absolute_tolerance,settings.objective_gap_relative_tolerance*abs(objectiveBefore));residual=max(0,max(A*winner-b));
assert(isfinite(gap)&&gap<=gapTolerance&&residual<=feasibilityTolerance,'Original exact2D global certificate failed: gap%g primal%g',gap,residual);
certificate=struct('backend','exact_2D_original_subproblem_active_set','global_objective_gap_upper_bound',gap,'global_objective_gap_tolerance',gapTolerance,...
    'maximum_normalized_constraint_violation',residual,'normalized_constraint_tolerance',feasibilityTolerance,'polygon_vertex_count',size(vertices,1),'finite_feasible_candidates',sum(isfinite(values)),...
    'original_subproblem_unchanged',true,'certified_without_conic_solver_status',true,'minorant_increment',value);
    function [value,g]=evaluate(x)
        if strcmp(mode,'MRT'),value=gradient'*x-curvature/2*(x'*x);g=gradient-curvature*x;
        else,r=base+G*x-q/2*(x'*x);if any(r<=0)||any(~isfinite(r)),value=-Inf;g=[NaN;NaN];return;end
        vectors=G-q.*x';change=G*x-q/2*(x'*x);if all(change./base>-1),value=sum(log1p(change./base))/log(2);else,value=sum(log(r./base))/log(2);end;g=sum(vectors./r,1)'/log(2);end
    end
    function [p,v,left,right,valid]=edge(index)
        p=A(index,:)'*b(index);v=[-A(index,2);A(index,1)];left=-Inf;right=Inf;valid=true;
        for row=1:size(A,1),slope=A(row,:)*v;remaining=b(row)-A(row,:)*p;
        if abs(slope)<1e-13,if remaining < -feasibilityTolerance,valid=false;return;end
        elseif slope>0,right=min(right,remaining/slope);else,left=max(left,remaining/slope);end
        end
        valid=isfinite(left+right)&&left<=right+feasibilityTolerance;
    end
    function endpoint=finiteEndpoint(endpoint,other,p,v)
        original=endpoint;
        for step=1:32,if isfinite(evaluate(p+endpoint*v)),return;end;endpoint=endpoint+sign(other-endpoint)*eps(max(1,abs(endpoint)));end
        for fraction=[1e-14 1e-12 1e-10 1e-8 1e-6],endpoint=original+fraction*(other-original);if isfinite(evaluate(p+endpoint*v)),return;end,end
        endpoint=[];
    end
    function derivative=edgeDerivative(parameter,p,v)
        [~,g]=evaluate(p+parameter*v);derivative=g'*v;
    end
end
