def passive_exact_candidate_QT_prefix(w, theta, r, c, iota):
    """Algorithm 1: original LDT/QT + sensing MM QCQP + scalar dual bisection."""
    fixed_channel_bundle = channels(theta, r, c)
    f = fixed_channel_bundle[0]
    k = len(c['noise'])
    fc, fs = (f[:, :k], f[:, k:])
    m = len(w)
    pd = np.asarray(c['desired_pattern'])
    den = iota * iota * float(pd @ pd)
    norms = np.sum(abs(fs) ** 2, axis=0)
    lip = 12 * c['power'] * norms ** 2 + 4 * iota * pd * norms
    spec = c['W_solver']
    history = [evaluate(w, theta, r, c, iota, _fixed_channel_bundle=fixed_channel_bundle)['utility']]
    records = []
    converged = False
    reason = 'maximum_iterations_without_criterion_stop'
    relative_objective = relative_step = None
    y = fc.conj().T @ w
    powers = abs(y) ** 2
    mask = np.ones_like(powers, dtype=bool)
    mask[np.arange(k), np.arange(k)] = False
    signal = powers[np.arange(k), np.arange(k)]
    interference = np.asarray(c['noise']) + np.sum(np.where(mask, powers, 0.0), axis=1)
    total = signal + interference
    mu = signal / interference
    eta = y[np.arange(k), np.arange(k)] / total
    q = fc * ((1 + mu) * abs(eta) ** 2)[None, :] @ fc.conj().T / np.log(2)
    p = np.zeros_like(w)
    p[:, :k] = fc * ((1 + mu) * eta)[None, :] / np.log(2)
    z = fs.conj().T @ w
    pattern = np.sum(abs(z) ** 2, axis=1)
    ga = 4 * fs @ ((pattern - iota * pd)[:, None] * z)
    q += c['rho'] * lip.sum() / (2 * den) * np.eye(m)
    p += c['rho'] / (2 * den) * (lip.sum() * w - ga)
    return dict(y=y, signal=signal, interference=interference, total=total, mu=mu, eta=eta, q=q, p=p, lip=lip, ga=ga)
