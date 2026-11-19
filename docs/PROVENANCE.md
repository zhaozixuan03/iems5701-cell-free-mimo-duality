# Source provenance and license

The five files under `upstream/` were fetched through the connected GitHub reader from [lorenzomiretti/duality](https://github.com/lorenzomiretti/duality), main at commit `5a968b40fa43e7d18b62641bb46073f57442f227` (19 April 2024). They were not edited. Their Git blob hashes are:

| File | Git blob SHA-1 |
|---|---|
| README.md | `5a4c3acad72b55df27b02ecc859d9e40cf4bf48f` |
| LICENSE | `d159169d1050894d3ea3b98e1c965c4058208fe1` |
| algorithm_convergence.py | `4979432f374fe398ef5883e09a6ac529760b801b` |
| local_vs_centralized_rate.py | `650688ca337b5758259ac91a0e4b503a4e457ac2` |
| main_problem.py | `aa78bd26954f096d3151ed592ba3bd176e2c6422` |

The upstream package states GPLv2. The full GPL-2.0 text is at the repository root and in `upstream/LICENSE`. The paper is [Miretti et al., IEEE Transactions on Signal Processing 72, 1750–1765, 2024](https://doi.org/10.1109/TSP.2024.3376809). The paper and course PDF are cited but not redistributed here.

The first shell clone attempt failed because the local proxy at 127.0.0.1:1086 was unavailable. A later direct-network clone succeeded into a sibling local directory, `duality-official-clone/`. Its HEAD is the commit above, and `cmp` confirmed all five `upstream/` files are byte-identical. That full official Git history was pushed unchanged to the [upstream-baseline branch](https://github.com/zhaozixuan03/iems5701-cell-free-mimo-duality/tree/upstream-baseline). The coursework main branch keeps its own separate baseline snapshot and project history.
