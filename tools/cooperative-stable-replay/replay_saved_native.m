function replay_saved_native(fixturePath,outDir,expectedSHA)
% Same saved full91 operands; continuous controls preserve their numeric value.
assert(~isfolder(outDir) && ~isfile(outDir),'Fresh output required');
assert(strcmp(hashfile(fixturePath),expectedSHA),'Saved fixture differs');
here=fileparts(mfilename('fullpath'));
production=fullfile(fileparts(fileparts(here)),'strict','cooperative-satcom'); addpath(production);
provider=fullfile(production,'evaluate_positive_wick.m');
assert(strcmp(which('evaluate_positive_wick'),provider));
sourceBefore=hashfile(provider); loaded=load(fixturePath,'stage_inputs');
assert(iscell(loaded.stage_inputs) && numel(loaded.stage_inputs)==91);
mkdir(outDir); outputs=cell(91,1); records=cell(91,1); beforeRng=rng;
for k=1:91
    x=loaded.stage_inputs{k};
    record=struct('case_ordinal',x.case_ordinal,'phase_stage',x.phase_stage,...
        'mode',x.mode,'computed',false,'error','','integer_smoothing_transport',isinteger(x.smoothing));
    try
        outputs{k}=evaluate_positive_wick(x.data,x.phi,x.mode,x.p,x.smoothing,x.limit,x.W);
        record.computed=true;
    catch exception
        record.error=exception.message;
    end
    records{k}=record;
end
save(fullfile(outDir,'native-all91-original-components.mat'),'outputs','records','-v7');
summary=struct('scope','All91 saved fullsize endpoint components; no new optimization',...
    'records',{records},'all91_returned',all(cellfun(@(x)x.computed,records)),...
    'integer_smoothing_controls_cast_exactly_to_double',sum(cellfun(@(x)x.integer_smoothing_transport,records)),...
    'fixture_SHA256',expectedSHA,'provider_SHA256',sourceBefore,...
    'source_and_input_unchanged',strcmp(sourceBefore,hashfile(provider)) && strcmp(expectedSHA,hashfile(fixturePath)),...
    'RNG_unchanged',isequal(beforeRng,rng),'full183_or_original_reference_pass',false);
fid=fopen(fullfile(outDir,'summary.json'),'w','n','UTF-8'); assert(fid>=0);
cleanup=onCleanup(@()fclose(fid)); fwrite(fid,jsonencode(summary),'char'); clear cleanup;
assert(summary.all91_returned && summary.source_and_input_unchanged && summary.RNG_unchanged);
end

function out=hashfile(path)
fid=fopen(path,'rb'); assert(fid>=0); cleanup=onCleanup(@()fclose(fid)); data=fread(fid,Inf,'*uint8'); clear cleanup;
md=java.security.MessageDigest.getInstance('SHA-256'); md.update(data);
out=lower(reshape(dec2hex(typecast(md.digest(),'uint8'),2).',1,[]));
end
