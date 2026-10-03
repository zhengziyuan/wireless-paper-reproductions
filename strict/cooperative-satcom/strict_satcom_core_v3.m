function varargout=strict_satcom_core_v3(action,varargin)
% Distinct numeric provider: only exact fixed sqrt(scale) factor in MR-QT.
% All other same original core actions are read-only delegated, SHA-bound.
if strcmp(action,'mr_qt_update')
    [varargout{1:nargout}]=strict_satcom_mr_qt_factored_v3(varargin{:});
else
    [varargout{1:nargout}]=strict_satcom_core(action,varargin{:});
end
end

