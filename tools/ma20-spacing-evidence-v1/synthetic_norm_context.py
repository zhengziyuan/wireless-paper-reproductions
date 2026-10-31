"""Synthetic row-context check; this is not the actual paper grid."""
import numpy as np

if np.__version__ != "2.5.3":
    raise ValueError("the recorded check used NumPy 2.5.3")
rng = np.random.default_rng(9192)
a = rng.normal(size=(144, 2))
a[0] = [0.0, 0.0]
a[1] = [0.5, 0.0]
a[2] = [np.nextafter(0.5, 0.0), 0.0]
a[3] = [np.nextafter(0.5, 1.0), 0.0]
a[143] = [0.0, 0.0]
j = 143
full = np.linalg.norm(a[:j] - a[j], axis=1)
checks = disagreements = 0
for i in range(j):
    for size in range(1, 6):
        pool = [k for k in range(j) if k != i]
        extra = rng.choice(pool, size - 1, replace=False).tolist()
        ix = sorted([i] + extra)
        value = np.linalg.norm(a[ix] - a[j], axis=1)[ix.index(i)]
        checks += 1
        disagreements += int(value.view(np.uint64) != full[i].view(np.uint64))
print({"numpy": np.__version__, "contexts": checks, "bitwise_disagreements": disagreements})
