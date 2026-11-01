function [out,info]=strict_satcom_ap_qt_scaled(W0,mu,C,Qgt,offset,powerLimit,interferenceLimit)
% Equivalent original complex AP QT: explicit SOC factors and scaled coordinates.
[J,N,U]=size(W0); before=strict_satcom_core('ap_evaluate',W0,mu,C,Qgt,offset);
z=complex(zeros(J,U)); upper=zeros(U,1);
for u=1:U
    for j=1:J
        m=reshape(mu(j,u,:),N,1); w=reshape(W0(j,:,u),N,1);
        z(j,u)=m'*w/before.denominator(u); upper(u)=upper(u)+powerLimit(j)*real(m'*m)/offset(u);
    end
end
objectiveScale=max(1e-6,min(upper)); factors=cell(J,U,U); gt=cell(J,size(Qgt,2));
for j=1:J
    for u=1:U
        m=reshape(mu(j,u,:),N,1);
        for i=1:U
            Q=reshape(C(j,u,:,:),N,N); if i~=u,Q=Q+m*m';end
            factors{j,u,i}=sqrt(sum(abs(z(:,u)).^2)*powerLimit(j)/objectiveScale)*factor(Q);
        end
    end
    for k=1:size(Qgt,2),gt{j,k}=sqrt(powerLimit(j)/interferenceLimit(k))*factor(reshape(Qgt(j,k,:,:),N,N));end
end
cvx_begin quiet
    variable V(N,U,J) complex
    variable scaledMinimum
    maximize(scaledMinimum)
    subject to
    for u=1:U
        linear=0; weighted=[];
        for j=1:J
            m=reshape(mu(j,u,:),N,1);
            linear=linear+2*real(conj(z(j,u))*(m'*V(:,u,j)))*sqrt(powerLimit(j))/objectiveScale;
            for i=1:U, weighted=[weighted;factors{j,u,i}*V(:,i,j)];end %#ok<AGROW>
        end
        t=linear-sum(abs(z(:,u)).^2)*offset(u)/objectiveScale-scaledMinimum;
        norm([2*weighted;t-1])<=t+1;
    end
    for j=1:J,norm(reshape(V(:,:,j),[],1))<=1;end
    for k=1:size(Qgt,2)
        weighted=[];
        for j=1:J,for i=1:U,weighted=[weighted;gt{j,k}*V(:,i,j)];end,end %#ok<AGROW>
        norm(weighted)<=1;
    end
cvx_end
assert(contains(cvx_status,'Solved'),'Scaled AP QT solver failed: %s',cvx_status);
out=complex(zeros(J,N,U));for j=1:J,out(j,:,:)=reshape(sqrt(powerLimit(j))*V(:,:,j),1,N,U);end
after=strict_satcom_core('ap_evaluate',out,mu,C,Qgt,offset);
originalSignal=complex(zeros(J,U));newSignal=originalSignal;
for j=1:J,for u=1:U
    m=reshape(mu(j,u,:),N,1);originalSignal(j,u)=m'*reshape(W0(j,:,u),N,1);newSignal(j,u)=m'*reshape(out(j,:,u),N,1);
end,end
qt=sum(2*real(conj(z).*originalSignal),1).'-sum(abs(z).^2,1).'.*before.denominator;
newqt=sum(2*real(conj(z).*newSignal),1).'-sum(abs(z).^2,1).'.*after.denominator;
physicalGamma=scaledMinimum*objectiveScale;
primal=max([0;(physicalGamma-newqt)./max(1,abs(newqt));after.satellite_power./powerLimit(:)-1;after.gt_interference./interferenceLimit(:)-1]);
diagnostics=struct('solver','external_CVX','status',cvx_status,'reported_solver_tolerance',cvx_slvtol,...
    'constraint_max_relative_violation',primal,'positive_objective_scale',objectiveScale,...
    'coordinate_change','W_j=sqrt(P_j)*V_j; identical feasible set','quadratic_form','Explicit PSD factors and rotated SOC');
info=struct('solver_status',cvx_status,'surrogate_minimum_sinr',physicalGamma,'solver_diagnostics',diagnostics,...
    'qt_bound_max_violation',max(0,physicalGamma-min(after.sinr)),'qt_tightness_error',max(abs(qt-before.sinr)),...
    'before',before,'after',after);
end

function F=factor(Q)
Q=(Q+Q')/2;[vectors,values]=eig(Q,'vector');values=real(values);
assert(min(values)>=-1e-9*max(1,max(abs(values))),'Source quadratic is not PSD');
F=diag(sqrt(max(values,0)))*vectors';
end

