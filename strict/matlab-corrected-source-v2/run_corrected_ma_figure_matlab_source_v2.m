function summary=run_corrected_ma_figure_matlab_source_v2(jobFolder,sourceFolder,outputFolder,configPath,executeSource)
% Full configured100x1000 corrected-source Figs14/16, independent MATLAB.
% New versioned MATLAB full-v2 trajectory; original numeric updates unchanged.
% No corrected position/curve runs until ALL300 source jobs are validated.
if nargin<4,configPath=fullfile(fileparts(jobFolder),'run_config.json');end
if nargin<5,executeSource=true;end
if ~isfolder(outputFolder),mkdir(outputFolder);end
if executeSource,run_full_ma_figure_v2(jobFolder,sourceFolder,configPath);end
config=jsondecode(fileread(configPath));manifest=jsondecode(fileread(fullfile(fileparts(jobFolder),'manifest.json')));plan=jsondecode(fileread(fullfile(fileparts(jobFolder),'plan.json')));
assert(ismember(plan.figure,[14 16])&&config.geometry_realizations==100&&config.nlos_realizations_per_geometry==1000);
assert(manifest.expected_jobs==300&&manifest.case_count==3&&manifest.realizations_per_case==100&&manifest.nlos_per_geometry==1000&&numel(manifest.files)==300&&manifest.input_bank_complete);
assert(strcmp(file_digest(configPath),manifest.config_sha256));assert(numel(plan.cases)==3);
assert(isequal(sort([plan.cases.point]),[5 10 15]));assert(all([plan.cases.M]==5));expectedN=6;if plan.figure==14,expectedN=8;end;assert(all([plan.cases.N]==expectedN));
entries=manifest.files;coverage=false(3,100);sourcePaths=cell(300,1);jobPaths=cell(300,1);valid=false(300,1);errors=cell(300,1);
for i=1:300
    entry=entries(i);a=entry.case_index+1;b=entry.realization+1;assert(a>=1&&a<=3&&b>=1&&b<=100&&~coverage(a,b));coverage(a,b)=true;
    stem=sprintf('case-%03d-mc-%03d',a-1,b-1);assert(strcmp(entry.filename,[stem '.json']));jobPaths{i}=fullfile(jobFolder,entry.filename);sourcePaths{i}=fullfile(sourceFolder,[stem '-matlab.json']);
    try
        [source,job,~,fp]=validate_corrected_zf_source_matlab_full_v2(jobPaths{i},sourcePaths{i},configPath);
        assert(strcmp(fp,entry.input_fingerprint)&&job.realization==b-1&&job.figure==plan.figure&&job.N==expectedN&&job.M==5);
        assert(abs(10*log10(job.kappa)-plan.cases(a).point)<1e-12);valid(i)=true;
    catch exception,errors{i}=exception.message;end
end
assert(all(coverage,'all'));summary=struct('paper_id','two-timescale-ma','figure',plan.figure,'scope','corrected_source_full_figure_original_model_Jensen_not_historical_recovery',...
    'matlab_source_version','MATLAB-full-v2-history-storage','corrected_adapter_version','corrected-source-MATLAB-full-v2','source_jobs_required',300,'source_jobs_verified',sum(valid),'full_source_execution_verified',all(valid),'geometries_per_kappa',100,'nlos_per_geometry',1000,...
    'Monte_Carlo_count_provenance','100 geometries and1000 NLoS are configured choices; source does not report original counts',...
    'errors',{errors},'printed_Eq74_75_recovered',false,'original_figure_complete',false,'original_curve_closeness_verified',false,...
    'historical_figure_recovery_claimed',false,'finite_ensemble_lower_bound_guaranteed',false,'corrected_source_figure_execution_complete',false);
write_json(fullfile(outputFolder,'source-readiness-matlab.json'),summary);
if ~all(valid),return;end
fingerprint=corrected_zf_source_v2_matlab_fingerprint(configPath);byCase=cell(3,1);for a=1:3,byCase{a}=cell(100,1);end
for i=1:300
    entry=entries(i);[~,stem]=fileparts(entry.filename);path=fullfile(outputFolder,[stem '-corrected-matlab.json']);reuse=false;
    if isfile(path)
        try
            result=jsondecode(fileread(path));source=jsondecode(fileread(sourcePaths{i}));
            reuse=strcmp(result.input_fingerprint,entry.input_fingerprint)&&strcmp(result.corrected_evaluator_source_sha256,fingerprint)&&...
                strcmp(result.source_result_sha256,file_digest(sourcePaths{i}))&&corrected_complete(result,source,expectedN);
        catch,reuse=false;end
    end
    if ~reuse
        if isfile(path),archive=fullfile(outputFolder,'retained-attempts');if ~isfolder(archive),mkdir(archive);end;[~,nonce]=fileparts(tempname(archive));copyfile(path,fullfile(archive,[stem '-' nonce '.json']));end
        result=evaluate_correlated_zf_matlab_source_v2(path,jobPaths{i},sourcePaths{i},configPath);
    end
    assert(strcmp(fingerprint,corrected_zf_source_v2_matlab_fingerprint(configPath)),'Versioned dependencies changed; do not mix scientific versions.');
    source=jsondecode(fileread(sourcePaths{i}));assert(corrected_complete(result,source,expectedN),'Every accepted position full evidence is required.');
    byCase{entry.case_index+1}{entry.realization+1}=result;
    progress=summary;progress.corrected_derivation_jobs_complete=i;progress.corrected_evaluator_source_sha256=fingerprint;
    write_json(fullfile(outputFolder,'derivation-progress-matlab.json'),progress);fprintf('Corrected source derivation %d/300\n',i);
end
panelNames={'source_layout_MC','exact_population_Jensen_plugin','MC_minus_Jensen_plugin','Jensen_outer_MC_delta_standard_error','Jensen_quadrature_rate_error_estimate'};
keys={'MC_mean','exact_population_Jensen_plugin','MC_minus_Jensen_plugin','Jensen_outer_MC_standard_error_delta_method','Jensen_quadrature_rate_error_estimate_first_order'};
panels=struct();models={'iid','correlated'};
for panel=1:numel(panelNames)
    series=cell(6,1);index=1;
    for a=1:3
        for model=1:2
            history=cell(100,1);
            for r=1:100,history{r}=byCase{a}{r}.histories.(models{model}).(keys{panel})(:).';assert(all(isfinite(history{r}))&&~isempty(history{r}));end
            count=max(cellfun(@numel,history));matrix=zeros(100,count);
            for r=1:100,matrix(r,:)=[history{r},repmat(history{r}(end),1,count-numel(history{r}))];end
            label='IID';if model==2,label='Correlated';end
            series{index}=struct('label',sprintf('%s, kappa=%g dB',label,plan.cases(a).point),'channel_model',models{model},'kappa_db',plan.cases(a).point,...
                'x',0:count-1,'y',mean(matrix,1),'geometry_standard_error_of_plotted_mean',std(matrix,0,1)/sqrt(100),'source_history_key',keys{panel});index=index+1;
        end
    end
    panels.(panelNames{panel})=series;
end
assert(strcmp(fingerprint,corrected_zf_source_v2_matlab_fingerprint(configPath)),'Versioned dependencies changed during full derivation.');
data=summary;data.corrected_source_figure_execution_complete=true;data.all300_corrected_derivations_complete=true;data.corrected_evaluator_source_sha256=fingerprint;
data.panels=panels;data.N=expectedN;data.M=5;data.data_kind='independent_full_configured_population_corrected_source_curves';
data.aggregation='all100 geometries and1000 identical exported draws per accepted unchanged iid Algorithm2 position; explicit final-state hold';
data.source_MC_or_formula_selection_disclosed='MC and corrected exact Jensen panels separate; original legend does not identify their historical numerical evaluator';
data.diagnostic_error_scope='adaptive quadrature error estimates and first-order delta standard errors are not interval certificates or confidence intervals';
write_json(fullfile(outputFolder,sprintf('ma-figure-%02d-corrected-matlab.json',plan.figure)),data);
render_panels(data,outputFolder);summary.corrected_source_figure_execution_complete=true;summary.corrected_derivation_jobs_complete=300;summary.panel_count=5;
write_json(fullfile(outputFolder,'derivation-summary-matlab.json'),summary);
end

function complete=corrected_complete(result,source,N)
complete=false;
try
    P=size(source.history.zf.positions,1);assert(result.trajectory_positions_evaluated==P&&numel(result.records)==P&&result.all_positions_full1000_MC_match_unchanged_source_receipt);
    for i=1:P
        if iscell(result.records),r=result.records{i};else,r=result.records(i);end
        assert(isequal(r.positions,reshape(source.history.zf.positions(i,:,:),N,2))&&r.nlos_samples==1000&&~r.trajectory_position_reoptimized);
        for model={'iid','correlated'}
            s=r.models.(model{1});a=s.actual_full1000_MC;b=s.exact_original_model_Jensen;
            assert(numel(a.sample_sum_rates)==1000&&all(isfinite(a.sample_sum_rates))&&abs(mean(a.sample_sum_rates)-a.mean_sum_rate)<1e-10);
            assert(numel(a.powers)==1000&&all(isfinite(a.powers))&&numel(a.off_diagonal_amplitude)==1000&&all(isfinite(a.off_diagonal_amplitude)));
            assert(isequal(size(s.direct_MC_inverse_diagonal_samples),[1000 5])&&all(isfinite(s.direct_MC_inverse_diagonal_samples),'all'));
            assert(isequal(size(b.conditional_inverse_moment_samples),[1000 5])&&all(isfinite(b.conditional_inverse_moment_samples),'all'));
            assert(isequal(size(b.conditional_quadrature_error_samples),[1000 5])&&all(isfinite(b.conditional_quadrature_error_samples),'all'));
            assert(s.all1000_times_M_Schur_identities_pass&&s.all1000_ZF_beamformer_rate_identities_pass&&b.outer_expectation_samples==1000);
            h=result.histories.(model{1});keys=fieldnames(h);for k=1:numel(keys),assert(numel(h.(keys{k}))==P&&all(isfinite(h.(keys{k}))));end
        end
    end
    complete=true;
catch,complete=false;end
end

function render_panels(data,outputFolder)
names=fieldnames(data.panels);styles={'-','--',':'};markers={'o','s','^'};colors=[.68 .24 .40;.16 .45 .64];
for panel=1:numel(names)
    f=figure('Visible','off','Units','inches','Position',[1 1 4.3 3.44],'Color','w');cleanup=onCleanup(@()close(f));ax=axes(f);hold(ax,'on');items=data.panels.(names{panel});
    for i=1:numel(items)
        item=items{i};model=1+strcmp(item.channel_model,'correlated');k=find([5 10 15]==item.kappa_db);
        plot(ax,item.x,item.y,'Color',colors(model,:),'LineStyle',styles{k},'Marker',markers{k},'MarkerIndices',1:max(1,floor(numel(item.x)/9)):numel(item.x),...
            'MarkerSize',3,'LineWidth',1.3,'DisplayName',item.label);
    end
    set(ax,'FontName','Times New Roman','FontSize',8.5,'Box','on','TickDir','in','XGrid','on','YGrid','on','GridAlpha',.2);
    xlabel(ax,'Accepted AO sweep index');ylabel(ax,'Rate (bps/Hz)');title(ax,strrep(names{panel},'_',' '),'Interpreter','none','FontSize',8.5);
    legend(ax,'Location','southoutside','NumColumns',2,'FontSize',7,'Box','on','Color','w');
    stem=fullfile(outputFolder,sprintf('ma-figure-%02d-corrected-%s-matlab',data.figure,names{panel}));exportgraphics(f,[stem '.png'],'Resolution',260);saveas(f,[stem '.svg']);clear cleanup;
end
end

function write_json(path,value)
folder=fileparts(path);if ~isempty(folder)&&~isfolder(folder),mkdir(folder);end
text=jsonencode(value,'PrettyPrint',true);temporary=[path '.tmp'];
for attempt=1:8
    fid=fopen(temporary,'w','n','UTF-8');if fid<0,error('Receipt I/O failed, not numerical failure');end;fprintf(fid,'%s',text);fclose(fid);
    [ok,message]=movefile(temporary,path,'f');if ok,return;end
    if attempt==8,error('Receipt I/O retry exhausted, not numerical failure: %s',message);end;pause(min(.1*2^(attempt-1),2));
end
end

function value=file_digest(path)
d=java.security.MessageDigest.getInstance('SHA-256');fid=fopen(path,'rb');assert(fid>=0);b=fread(fid,Inf,'*uint8');fclose(fid);d.update(b);raw=typecast(d.digest(),'uint8');value=lower(reshape(dec2hex(raw,2).',1,[]));
end
