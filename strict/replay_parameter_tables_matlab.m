function result = replay_parameter_tables_matlab(repo, outputPath)
% Independent native numeric-parameter replay; no optimization/measurement claim.
packet=fullfile(repo,'strict','validation','parameter-tables-source-qualified-v1');
mapping=jsondecode(fileread(fullfile(packet,'actual-source-table-read-and-mapping-v1.json')));
contract=jsondecode(fileread(fullfile(packet,'canonical-parameter-contract-v1.json')));
rawContract=fileread(fullfile(packet,'canonical-parameter-contract-v1.json'));
% jsondecode sanitizes path keys; retain literal paths for byte verification.
section=regexp(rawContract,'"canonical_file_sha256"\s*:\s*\{([^}]+)\}','tokens','once');
assert(~isempty(section),'Missing canonical source bindings');
pairs=regexp(section{1},'"([^"]+)"\s*:\s*"([0-9a-f]{64})"','tokens');
assert(~isempty(pairs),'No canonical source bindings');
for j=1:numel(pairs)
    path=fullfile(repo,strrep(pairs{j}{1},'/',filesep));
    fid=fopen(path,'rb');assert(fid>=0,'Missing canonical source');
    cleanup=onCleanup(@()fclose(fid));bytes=fread(fid,Inf,'*uint8');clear cleanup;
    md=java.security.MessageDigest.getInstance('SHA-256');md.update(bytes);
    actual=lower(reshape(dec2hex(typecast(md.digest(),'uint8'),2).',1,[]));
    assert(strcmp(actual,pairs{j}{2}),'Canonical source/configuration differs');
end
coop=jsondecode(fileread(fullfile(repo,'strict','cooperative-satcom','spectral_config.json')));
hot=jsondecode(fileread(fullfile(repo,'strict','hotspot-satcom','instantaneous_geometry_config.json')));
coop=coop.reported;hot=hot.reported;
py=fileread(fullfile(repo,'strict','hotspot-satcom','run_statistical_validated.py'));
mat=fileread(fullfile(repo,'strict','hotspot-satcom','run_strict_hotspot_statistical_validated.m'));
assert(contains(py,'kappa_ground_db=20,nhu_statistical_sinr_db=-3')&&...
    contains(mat,'kappa_ground_db=20')&&contains(mat,'nhu_statistical_sinr_db=-3'),...
    'Statistical source overrides do not match canonical bindings');
hot.kappa_ground_statistical_db=20;hot.nhu_statistical_sinr_db=-3;
tables=to_cells(mapping.tables);rows={};numericCount=0;patternCount=0;
for t=1:numel(tables)
    table=tables{t};if strcmp(table.paper,'cooperative-satcom'),values=coop;else,assert(strcmp(table.paper,'hotspot-satcom'));values=hot;end
    parameters=to_cells(table.parameter_rows);
    for k=1:numel(parameters)
        row=parameters{k};bindings=to_cells(row.bindings);checks={};
        for b=1:numel(bindings)
            binding=bindings{b};assert(isfield(values,binding.config_key),'Missing canonical parameter');
            expected=binding.expected_SI_or_declared_value;observed=values.(binding.config_key);
            assert(isequal(size(expected),size(observed))||isvector(expected)&&isvector(observed),'Parameter dimensions differ');
            passed=isequaln(expected(:),observed(:));assert(passed,'Canonical parameter does not match source mapping');
            checks{end+1}=struct('key',binding.config_key,'expected',expected,'observed',observed,'passed',passed); %#ok<AGROW>
        end
        if isempty(bindings),patternCount=patternCount+1;else,numericCount=numericCount+1;end
        rows{end+1}=struct('paper',table.paper,'parameter_id',row.parameter_id,'source_line',row.source_line,...
            'has_numeric_parameter_binding',~isempty(bindings),'checks',{checks},'machine_bindings_pass',true,...
            'pattern_or_realized_geometry_certified',false); %#ok<AGROW>
    end
end
assert(numel(rows)==36&&numericCount==34&&patternCount==2,'Incomplete original table population');
result=struct('scope','Native MATLAB canonical-byte and numeric-parameter replay of two retained author-source mappings',...
    'execution_engine','MATLAB_native_jsondecode_parameter_replay','matlab_version',version,...
    'all36_row_mappings_checked',true,'all34_numeric_parameter_rows_match',true,...
    'all_canonical_bytes_match_recorded_source_evidence',true,'canonical_files_checked',numel(pairs),...
    'two_external_pattern_reference_rows_are_not_certified',true,'rows',{rows},...
    'all_pairwise_realized_geometry_checks_performed',false,'full_figure_optimization_performed',false,...
    'author_source_hashes',contract.author_source_hashes,'final_publisher_table_equivalence_verified',false);
assert(~isfile(outputPath),'Preserve existing result');
[parent,~,~]=fileparts(outputPath);if ~isfolder(parent),mkdir(parent);end
fid=fopen(outputPath,'w','n','UTF-8');assert(fid>=0);cleanup=onCleanup(@()fclose(fid));
fprintf(fid,'%s\n',jsonencode(result));
end

function out=to_cells(value)
if iscell(value),out=value;elseif isempty(value),out={};else,out=num2cell(value);end
end
