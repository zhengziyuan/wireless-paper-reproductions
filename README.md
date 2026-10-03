# Wireless paper reproductions

> **Strict-reproduction status (2026-10-03): NOT COMPLETE.** The owner now requires the original theoretical algorithms and full published simulation scenarios, without substitute solvers or reduced dimensions/budgets. The previous `papers/` release does **not** meet that requirement and is retained only as a superseded preview. Its 6/6 parity result is not evidence of strict or complete paper reproduction.
>
> **严格复现状态：尚未完成。** 之前的 `papers/` 为已撤下推荐的简化预览，含替代子求解器及缩小场景，不满足现在的要求。严格版工作位于 [`strict/`](strict/README.md)。未公开的逐图参数、最终稿和原文歧义必须先补齐；不得自行编造设置或用替代算法补位。

Independent MATLAB and Python implementations associated with selected technical papers by Ziyuan Zheng and collaborators.

This is not the original private simulation source. Each paper has an explicit implementation scope, equation/source map, shared inputs, executable examples, and validation results. A successful reduced-size run is not evidence that every published figure, Monte Carlo campaign, or hardware experiment has been reproduced.

中文说明：本仓库提供六篇技术论文的独立 MATLAB/Python 双实现，采用相同数值输入进行模型、梯度、约束和双语言结果检查。这是限定范围的核心实现，不是原作者私有代码，也不是原论文全部图表或硬件实验的完整复现。每篇目录均列明算法改动和未完成部分；Hotspot SatCom 的最终期刊全文核验仍待完成。

## Superseded preview packages (not the strict implementations)

| Package | Paper DOI | Implemented core |
| --- | --- | --- |
| [MIS communications](papers/mis-communications) | [TWC.2025.3621083](https://doi.org/10.1109/TWC.2025.3621083) | Two-layer aperture, exact scheduling, soft-min phase optimization |
| [MIS sensing](papers/mis-sensing) | [JSTSP.2026.3681476](https://doi.org/10.1109/JSTSP.2026.3681476) | Fourth-order echo SINR, exact scheduling, reduced augmented-Lagrangian optimization |
| [Rotatable-array ISAC](papers/rotatable-isac) | [JSTSP.2026.3693227](https://doi.org/10.1109/JSTSP.2026.3693227) | Rotation-aware channels, rate/NMSE model, disclosed alternative AO subsolvers |
| [Two-timescale movable antennas](papers/two-timescale-ma) | [TCOMM.2025.3585515](https://doi.org/10.1109/TCOMM.2025.3585515) | MRT statistical AO/SCA position optimization; ZF evaluation only |
| [Cooperative SatCom](papers/cooperative-satcom) | [JSAC.2024.3460068](https://doi.org/10.1109/JSAC.2024.3460068) | Noncoherent MR LoS limit, RIS phase optimization, restricted power allocation |
| [Hotspot SatCom](papers/hotspot-satcom) | [TWC.2023.3309957](https://doi.org/10.1109/TWC.2023.3309957) | Thesis-cross-checked RIS decorrelation core + separate ZF/QoS baseline; final journal full text pending |

The npj Wireless Technology perspective is not a numerical-algorithm package and is not included. Every package contains `README.md`, `source_map.json`, `fixture.json`, a Python entry point, and a uniquely named MATLAB entry point.

## Dependencies

Python 3.10 or later and NumPy. MATLAB implementations use base MATLAB unless a paper README explicitly states otherwise. Optional plotting uses Matplotlib. No proprietary solver or third-party MATLAB toolbox is bundled.

```sh
python -m pip install -r requirements.txt
```

## Run and validate

From this repository's root, run all Python examples and checks:

```sh
python scripts/run_python.py
python scripts/validate_python.py
python -m unittest discover -s tests -v
```

In MATLAB, from this repository's root:

```matlab
addpath('scripts');
run_all_matlab;
```

Only after actually running both languages:

```sh
python scripts/validate_parity.py
python scripts/plot_histories.py
```

For one package: `python scripts/run_python.py --paper mis-communications` and `run_all_matlab('mis-communications')`. The `outputs/` folder is generated and ignored by Git. The checked-in [validation evidence](validation) records actual local outputs, parity thresholds, runtime versions, and fixture/source SHA-256 hashes. It is not a substitute for running your own changed fixture.

The initial local checks use Python 3.12, NumPy, and MATLAB R2025b. Numerical parity uses absolute tolerance `1e-7` plus relative tolerance `1e-6` on complete outputs, including iteration histories. Machine-scale deterministic tie breaking is documented in the MIS packages. GitHub Actions reruns Python core checks only; MATLAB parity is a separate licensed-runtime local check.

![Reduced-fixture optimization histories](validation/iteration-traces.png)

These are newly computed iteration traces, **not published paper figures**. Metrics and units differ between panels and cannot be compared across papers.

## Scientific scope

- MATLAB and Python use the same input fixtures, rather than assuming different language random generators produce the same samples.
- Tests distinguish model identities, constraint feasibility, numerical gradient checks, optimizer behavior, and cross-language numerical agreement.
- Original measurement data, hardware controls, manuscript files, reviewer correspondence, and private institutional material are excluded.
- Neither convergence to a global optimum nor agreement with every published curve is implied.

## Rights and citations

Please cite the corresponding paper when using its model. This repository does not redistribute the papers or third-party solvers. No open-source license has been selected yet; public visibility alone is not a grant of an open-source license.
