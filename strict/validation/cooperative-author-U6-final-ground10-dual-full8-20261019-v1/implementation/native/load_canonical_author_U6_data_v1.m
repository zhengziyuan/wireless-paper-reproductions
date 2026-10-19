function [data,power_limit,interference_limit]=load_canonical_author_U6_data_v1(path,configuration)
% IO-only: native uses exactly the saved canonical11fields, no geometry factory.
a=load(path,'data','power_limit','interference_limit','transport_metadata');
assert(strcmp(a.transport_metadata.schema,'canonical-native-U6-exact-NPZ-to-MAT-format-only-v1'));
assert(strcmp(a.transport_metadata.input_npz_SHA256,'ca584f9bdf3eb551f8399026c82693c8072cb7c10e1e198baf29f8a7d5f93353'));
assert(strcmp(a.transport_metadata.stage,'enabled'));
assert(configuration.physical_input_variant.requires_explicit_saved_factory && strcmp(configuration.physical_input_variant.stage,'enabled'));
p=configuration.reported;assert(p.J==3&&p.U==6&&p.N==16&&p.M==25&&p.K==1&&p.power_w==50);
assert(p.kappa_leo_db==20&&p.kappa_ground_db==10&&p.kappa_geo_db==30&&p.interference_to_noise_ratio==.01);
assert(configuration.physical_input_variant.source_linear_beta_R==1&&configuration.physical_input_variant.selected_linear_beta_R==10,'Retain original sourcebeta1 versus selected finalbeta10');
data=a.data;power_limit=a.power_limit;interference_limit=a.interference_limit;
names={'d_mean','d_var','G_mean','G_var','r_mean','r_var','gt_second','geo_d_mean','geo_d_var','geo_G_mean','geo_G_var'};
shapes={[3,6,16],[3,6],[3,6,16,25],[3,6],[6,25],[6,1],[3,1,16,16],[6,1],[6,1],[6,25],[6,1]};
assert(isequal(sort(fieldnames(data)),sort(names(:))));
for k=1:numel(names)
    v=data.(names{k});assert(isa(v,'double')&&isequal(size(v),shapes{k})&&all(isfinite(v(:))),['Canonical savedfield shape/class/domain: ',names{k}]);
end
assert(isequal(size(power_limit),[3,1])&&isequal(power_limit,50*ones(3,1)));
assert(isequal(size(interference_limit),[1,1])&&interference_limit==.01);
% No scale/symmetrize/project/phase operation is applied to returned arrays.
end
