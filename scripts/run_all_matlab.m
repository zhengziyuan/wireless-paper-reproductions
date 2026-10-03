function run_all_matlab(paper_id, output_dir, legacy_preview)
% Superseded reduced previews only; explicit third argument true is required.
% Current original-algorithm full-scene commands are in strict/README.md.
arguments
    paper_id (1,:) char = 'all'
    output_dir (1,:) char = ''
    legacy_preview (1,1) logical = false
end
if ~legacy_preview
    error('reproduction:legacyPreviewDisabled', ...
        'Reduced historical previews are disabled by default. Use strict/README.md; opt in explicitly only for old previews.');
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
