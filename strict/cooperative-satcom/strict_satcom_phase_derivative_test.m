function result=strict_satcom_phase_derivative_test(fixturePath,outputPath)
% Same full-size physical inputs; independent scalar-coordinate and Py/MAT checks.
f=load(fixturePath);cases={};
for tts=[false,true]
    if tts,p=f.p_tts;name='MR-TTS';referenceValue=f.MR_TTS_value;referenceGradient=f.MR_TTS_gradient;
    else,p=f.p_stat;name='MR-S';referenceValue=f.MR_S_value;referenceGradient=f.MR_S_gradient;end
    [value,g]=strict_satcom_models('mr_phase',f.data,f.phi,p,f.smoothing,f.limit,tts);
    [old,oldg]=strict_satcom_models('mr_phase_reference',f.data,f.phi,p,f.smoothing,f.limit,tts);
    cases{end+1}=struct('scheme',name,'scalar_value_error',max(abs(value-old)), ...
        'scalar_gradient_error',max(abs(g(:)-oldg(:))), ...
        'python_value_error',max(abs(value-referenceValue)), ...
        'python_gradient_error',max(abs(g(:)-referenceGradient(:)))); %#ok<AGROW>
end
[value,g]=strict_satcom_models('ap_phase',f.data,f.phi,f.W);[old,oldg]=strict_satcom_models('ap_phase_reference',f.data,f.phi,f.W);
cases{end+1}=struct('scheme','AP','scalar_value_error',max(abs(value(:)-old(:))), ...
    'scalar_gradient_error',max(abs(g(:)-oldg(:))),'python_value_error',max(abs(value(:)-f.AP_value(:))), ...
    'python_gradient_error',max(abs(g(:)-f.AP_gradient(:))));
passed=true;for k=1:numel(cases),c=cases{k};passed=passed&&c.scalar_value_error<1e-10&&c.scalar_gradient_error<1e-10&&c.python_value_error<1e-10&&c.python_gradient_error<1e-10;end
result=struct('scope','full_dimension_derivative_contraction_component_test_NOT_full_reproduction', ...
    'dimensions',struct('J',3,'U',2,'N',16,'M',25,'K',1),'cases',{cases},'all_passed',passed,'full_reproduction_pass',false);
folder=fileparts(outputPath);if ~exist(folder,'dir'),mkdir(folder);end
fid=fopen(outputPath,'w');assert(fid>=0);cleanup=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(result));
assert(passed,'Independent exact derivative contraction parity failed');
end
