function run_all_matlab(paper_id, output_dir)
% Run deterministic independent implementations; this is not an original-figure campaign.
arguments
    paper_id (1,:) char = 'all'
    output_dir (1,:) char = ''
end
root = fileparts(fileparts(mfilename('fullpath')));
if isempty(output_dir), output_dir = fullfile(root, 'outputs', 'matlab'); end
if ~isfolder(output_dir), mkdir(output_dir); end
papers = jsondecode(fileread(fullfile(root, 'papers.json')));
matched = false;
for n = 1:numel(papers)
    item = papers(n);
    if ~strcmp(paper_id, 'all') && ~strcmp(paper_id, item.id), continue; end
    matched = true;
    folder = fullfile(root, 'papers', item.id);
    addpath(folder);
    cleanup = onCleanup(@() rmpath(folder));
    feval(item.matlab_entry, fullfile(output_dir, [item.id '.json']));
    fprintf('Completed %s\n', item.id);
    clear cleanup;
end
if ~matched, error('reproduction:unknownPaper', 'Unknown paper id. See papers.json.'); end
end
