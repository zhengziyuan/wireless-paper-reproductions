function result=strict_hotspot_element_count(reference,count)
% Exact author Fig3-9 count-only aperture scaling. Centers remain fixed.
% reference is the full finite-Rician28000-element scenario/shared fixture.
assert(ismember(count,4000:4000:28000),'Exact original seven-count grid required');
assert(size(reference.cascade,2)==25,'All25 original subsurfaces required');
% MAT fixtures can store exact counts as int64; floating-point arithmetic is
% required for field scaling, not integer division or integer square roots.
count=double(count);
result=reference;ratio=count/28000;field=sqrt(ratio);
result.cascade=reference.cascade*ratio;
result.mean_inputs.matrix_mean=reference.mean_inputs.matrix_mean*field;
result.mean_inputs.ground_mean=reference.mean_inputs.ground_mean*field;
result.mean_inputs.matrix_variance=reference.mean_inputs.matrix_variance*ratio;
result.mean_inputs.ground_variance=reference.mean_inputs.ground_variance*ratio;
result.aperture_count_contract=struct('elements_per_subsurface',count,'reference_elements_per_subsurface',28000, ...
    'fixed_subpanel_centers',true,'ground_phase_changed_by_count',false,'RIS_phase_dimension',25, ...
    'two_link_field_multiplier',field,'cascade_field_multiplier',ratio, ...
    'row_column_factorization_inferred',false,'original_author_geometry_recovered',false);
end
