function strict_satcom_positive_wick_test()
% Exact non-Gaussian scalar witness, not a reduced paper campaign.
d=struct('d_mean',complex(reshape(0,1,1,1)),'d_var',4,...
    'G_mean',complex(reshape(1,1,1,1,1)),'G_var',2,'r_mean',complex(0),'r_var',3,...
    'gt_second',complex(reshape(0,1,1,1,1)),'geo_d_mean',complex(0),...
    'geo_d_var',0,'geo_G_mean',complex(0),'geo_G_var',0);
x=evaluate_positive_wick(d,complex(1),'mr_tts',1,int64(1),1,[]);
assert(x.tts_power==13 && x.fourth==482 && x.tts_own==313);
assert(x.numerator==169 && x.denominator==314 && x.criterion==169/314-1);
assert(x.gradient==0);
fprintf('Exact scalar non-Gaussian fourth moment and integer1 transport passed.\n');
end
