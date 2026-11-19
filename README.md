# Cell-free Massive MIMO：复现与计算加速

本项目复现 [Miretti 等人的论文](https://doi.org/10.1109/TSP.2024.3376809)中的 Figure 2 和 Figure 3，并加快作者程序的计算。论文代码来自[作者仓库](https://github.com/lorenzomiretti/duality)。

## 我们做了什么

- **保存原版**：`upstream/` 中的五个文件与作者提交 [`5a968b4`](https://github.com/lorenzomiretti/duality/commit/5a968b40fa43e7d18b62641bb46073f57442f227)逐字节相同；作者原有的 Git 历史另存于 [`upstream-baseline` 分支](https://github.com/zhaozixuan03/iems5701-cell-free-mimo-duality/tree/upstream-baseline)。原版文件未改动，来源和许可证见 [docs/PROVENANCE.md](docs/PROVENANCE.md)。
- **Figure 3**：运行作者原始脚本，保存对偶目标值和最大 AP 功率两张图。然后在相同随机样本上比较原版与加速版。
- **Figure 2**：完成 8 个速率 × 2 种 CSI × 每组 100 个网络样本，共 1600 个。较慢的样本用恢复的原始随机数状态并行续跑；每个样本仍使用作者的求解器参数、四次重试和判定规则。

## 加速方法：为什么做、做了什么

作者的本地 CSI 求解器要对每个信道样本重复做小矩阵求逆和逐个累加。我们把同一批信道样本堆叠起来，让 NumPy 一次处理整批矩阵，并用线性方程求解替代“先求逆、再相乘”。预期是在**不改变数学问题和迭代规则**的前提下，减少每次迭代的计算时间。改动位于 [optimized_problem.py](optimized_problem.py)，集中式 CSI 仍调用原版实现。

这是一个**已测得成功的计算加速**，不是新的无线性能算法。它没有减少迭代次数，也没有提高可行率；这两点不应作为改进收益。若下一步专门追求更少的迭代，需要另设算法对照，不能把本次速度提升说成收敛次数改善。

## 实际结果

| 检查 | 结果 |
| --- | --- |
| Figure 2 样本 | 1600 个；原版和加速版均有 1599 个被作者算法判定为已求解 |
| Figure 2 两版对照 | 每个样本的求解状态、每 AP/总功率可行性、重试次数和外层迭代数全部一致 |
| Figure 3 时间对照 | 5 个随机种子，每个重复 5 次，交替运行顺序；各随机种子的加速比中位数再取中位数为 **7.38 倍** |
| Figure 3 累计求解时间 | 原版 71.02 秒；加速版 9.69 秒，共 25 次配对 |
| Figure 3 数值一致性 | 25 次配对的内外层迭代数均一致；最大目标值差 `2.30e-10 mW`，最终 AP 功率最大差 `4.39e-11 mW` |

这些时间来自一台 macOS arm64 机器、Python 3.12 和单线程 OpenBLAS；换机器可能不同。Figure 2 中速率为 4 bit/s/Hz 时，每 AP 功率约束下，本地 CSI 的可行比例为 0.18，集中式 CSI 为 0.43；总功率约束下分别为 0.31 和 0.83。比例按**已求解的样本**计算，与作者脚本一致；完整表格和 95% Wilson 区间见 [Figure 2 结果目录](results/figure2_full/)。

**为什么 seed 6 不可行？** Figure 3 的额外随机样本 seed 6 要求最低速率 3.5 bit/s/Hz。作者算法在第一次外层迭代得到约 `17,933.51 mW` 的对偶目标值，超过 16 个 AP 合计 `16,000 mW` 的功率上限，因此按作者程序的判定规则标记为“已求解但不可行”。当时报告的最大 SINR 缺口为 `1.0349`，最大单 AP 功率超限约 `2,046.53 mW`。原版和加速版对此一致；这反映该随机网络样本较难满足约束，而非加速版算错。Figure 3 原论文使用的是 seed 4，seed 6 是额外的稳健性检查。

## 图片和原始数据

- [Figure 2 完整曲线与抽样区间](results/figure2_full/figure2_with_ci.png)
- [Figure 3 原始对偶目标值曲线](results/figure3_official/dual_objective.png)
- [Figure 3 原始最大 AP 功率曲线](results/figure3_official/max_power.png)
- [25 次配对计时](results/figure3_repeats/timings.csv)和[汇总](results/figure3_repeats/summary.json)
- [完整实验记录](docs/EXPERIMENT_LOG.md)：参数、运行命令、数值对照、边界样本和局限

## 重新运行

Python 3.12；依赖见 [requirements.txt](requirements.txt)。以下命令从仓库根目录执行。Figure 2 两种求解器应分开运行，以免机器负载影响计时。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg MPLCONFIGDIR=/tmp
python experiments/run_official_figure3.py
python experiments/finish_figure2_parallel.py --workers 6
python experiments/finish_figure2_parallel.py --optimized --workers 4
python experiments/compare_full_figure2.py
python experiments/analyze_full_figure2.py
python experiments/benchmark_repeats.py
```

Figure 2 的续跑程序逐个保存完成的样本，可以从已有记录继续。`results/` 内包含原始输出、配置、随机种子、失败或未收敛的案例及图表。

## 来源与许可证

作者代码注明 GPLv2；本仓库保留原有版权与许可证声明，并以 GPL-2.0-only 发布衍生代码，见 [LICENSE](LICENSE)。使用论文或代码开展研究时请引用[原论文](https://doi.org/10.1109/TSP.2024.3376809)。GitHub 的 Contributors 图通常只统计默认分支上的提交；作者的原始提交保存在 `upstream-baseline`，因此默认分支的图只显示本项目的提交者。这不改变作者代码的归属。
