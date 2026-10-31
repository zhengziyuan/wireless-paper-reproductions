function result=solve_fixed_original_qcqp_matlab_v1(inputPath,outputPath)
% Same one captured original QCQP, factored Pcomm and positive original alpha.
% No outer optimizer/MC/new sample, no Q eig/clamp/jitter or changed tolerance.
x=load(inputPath);W=x.w;fc=x.fc;mu=x.mu(:);eta=x.eta(:);lip=x.lip(:);Ga=x.ga;
den=x.den;rho=x.rho;power=x.power;tol=x.bisection_tolerance;[M,K]=size(fc);
assert(K<=M&&size(W,1)==M&&size(W,2)>=K&&isequal(size(Ga),size(W)));
assert(den>0&&rho>0&&power>0&&tol>0&&all(mu>=0));
assert(all(isfinite([W(:);fc(:);mu(:);eta(:);lip(:);Ga(:)])));
alpha=rho*sum(lip)/(2*den);beta=rho/(2*den);assert(alpha>0);
root=sqrt(1+mu)/sqrt(log(2));magnitude=abs(eta);scale=root.*magnitude;
gamma=complex(zeros(K,1));active=magnitude~=0;gamma(active)=root(active).*(eta(active)./magnitude(active));
factor=fc.*transpose(scale);[L,S,V]=svd(factor);singular=diag(S);sigma2=[singular.^2;zeros(M-K,1)];
commCoordinates=complex(zeros(size(W)));
% gamma is not conjugated in the paper's communication P.
commCoordinates(1:K,1:K)=(singular.*V').*transpose(gamma);
projectedW=L'*W;projectedGa=L'*Ga;
senseCoordinates=alpha*projectedW-beta*projectedGa;
coordinates=commCoordinates+senseCoordinates;row=sum(abs(coordinates).^2,2);diagonal=alpha+sigma2;
transmit=@(nu)sum(row./(diagonal+nu).^2);nu=0;bisects=0;doublings=0;lo=[];hi=[];
if transmit(0)>power
    lo=0;hi=1;while transmit(hi)>power,hi=2*hi;doublings=doublings+1;end
    while hi-lo>tol*max(1,hi)
        mid=(lo+hi)/2;if transmit(mid)>power,lo=mid;else,hi=mid;end;bisects=bisects+1;
    end
    nu=hi;
end
solution=L*(coordinates./(diagonal+nu));
reconstructedComm=complex(zeros(size(W)));reconstructedComm(:,1:K)=factor.*transpose(gamma);
reconstructedSense=alpha*W-beta*Ga;
result=struct('solution',solution,'alpha',alpha,'beta',beta,'nu',nu,'bisection_steps',bisects,'bracket_doublings',doublings,...
    'bracket_lo',lo,'bracket_hi',hi,'power_from_basis',transmit(nu),'actual_binary64_power',sum(abs(solution(:)).^2),...
    'original_power_cap',power,'bisection_tolerance',tol,'factor',factor,'left',L,'singular',singular,'right_h',V',...
    'gamma',gamma,'comm_coordinates',commCoordinates,'sensing_coordinates',senseCoordinates,'total_coordinates',coordinates,...
    'original_positive_diagonal',diagonal,'reconstructed_communication_P',reconstructedComm,'reconstructed_sensing_P',reconstructedSense,...
    'no_actual_bad_Q_or_assembled_communication_P_used',true,'exact_zero_eta_branch_only',true,'no_rank_threshold_clamp_jitter_or_eigh',true);
save(outputPath,'result','-v7');
end
