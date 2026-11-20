# Cell-free Massive MIMO：论文复现、求解加速与等预算 AP 分配

本项目复现 [Miretti 等人的论文](https://doi.org/10.1109/TSP.2024.3376809)中的 Figure 2 和 Figure 3，并验证两类改进：减少求解计算，以及在相同总 CSI 连接预算下提高无线约束可行率。论文代码来自[作者仓库](https://github.com/lorenzomiretti/duality)。

## 核心结果

在 60 个独立验证网络中，固定每人连接 4 个 AP 时有 **31 个**在预算内找到可行解；重新分配相同的 64 条 AP–用户连接后有 **41 个**。逐网络是新增成功 10 个、失去成功 0 个。另一项 Anderson 求解改进在单独的 30 个网络中把内层迭代数从 **3880** 降到 **3019**。两项改进解决不同问题，完整对照与边界见下文。

## 我们做了什么

- **保存原版**：`upstream/` 中的五个文件与作者提交 [`5a968b4`](https://github.com/lorenzomiretti/duality/commit/5a968b40fa43e7d18b62641bb46073f57442f227)逐字节相同；作者原有的 Git 历史另存于 [`upstream-baseline` 分支](https://github.com/zhaozixuan03/iems5701-cell-free-mimo-duality/tree/upstream-baseline)。原版文件未改动，来源和许可证见 [docs/PROVENANCE.md](docs/PROVENANCE.md)。
- **Figure 3**：运行作者原始脚本，保存对偶目标值和最大 AP 功率两张图。然后在相同随机样本上比较原版与加速版。
- **Figure 2**：完成 8 个速率 × 2 种 CSI × 每组 100 个网络样本，共 1600 个。较慢的样本用恢复的原始随机数状态并行续跑；每个样本仍使用作者的求解器参数、四次重试和判定规则。
- **新的 AP 分配**：在不增加总 CSI 连接数或 AP 功率上限的条件下，让弱用户连接更多 AP，并用全新网络检验最低速率是否更容易达到。

## 加速方法：为什么做、做了什么

实测结果：在 Figure 3 的 25 次配对计时中，相对作者原版的每种子中位加速比为 **8.90 倍**，内外层迭代数及最终数值在所报告的精度内一致。原因是作者的本地 CSI 求解器要对每个信道样本重复做小矩阵求逆和逐个累加。我们把样本堆叠起来批量求解矩阵方程，并复用内层连续两步中输入相同的线性响应。改动位于 [optimized_problem.py](optimized_problem.py)，集中式 CSI 仍调用原版实现；复用的独立对照见 [docs/RESPONSE_REUSE.md](docs/RESPONSE_REUSE.md)。

这是一个 **已测得成功的单轮计算加速**，本身没有改变迭代次数或可行率。

## 新的收敛改进：减少内层功率迭代

实测结果：在另 30 个新网络中，内层功率迭代数从 **3880 降到 3019**，总求解时间从 **24.60 降到 19.41 秒**，两版成功数均为 **15/30**。作者算法每次调整 AP 约束权重后，会反复更新 UE 功率直到接近固定点。我们加入带保护的 Anderson 加速：利用近期变化提出下一步功率；候选不合理时采用作者原更新。第一次外层迭代保留作者的不可行性初筛，外层步长和外层停止规则不变。它减少的是 **内层轮数**，与前述每轮矩阵计算优化不同。代码见 [anderson_problem.py](anderson_problem.py)，规则与实验见 [docs/ANDERSON_ACCELERATION.md](docs/ANDERSON_ACCELERATION.md)。

## 已验证的无线系统改进：相同总连接数下提高可行率

独立验证结果：在目标速率 3.5 bit/s/Hz 的 60 个新网络中，原规则找到可行解 **31/60**，新规则 **41/60**；逐网络新增成功 10 个、失去成功 0 个。其中 9 个新增案例的原规则被求解器判为不可行，另 1 个原规则在迭代预算内未解出。这说明我们改进的是在相同目标速率与每 AP 功率上限下，网络 **找到满足约束的解的比例**，不只是程序运行速度。

做法是把原来每位用户固定 4 个 AP、总共 **64 条 AP–用户 CSI 连接**，按长期信道条件重新分配：最弱 4 人各连接其最强的 6 个 AP，中间 8 人各连接 4 个，最强 4 人各连接 2 个。总连接数、目标速率和发射功率上限保持一致。代价是这 60 个网络的总求解时间从 **64.25 秒增至 71.97 秒**，约增加 12%；单个用户得到的 CSI 连接数也不同。方法在其他系统规模和信道模型下仍需验证。代码见 [variable_q_problem.py](variable_q_problem.py)，公平对照、全部参数和逐样本结果见 [docs/VARIABLE_Q.md](docs/VARIABLE_Q.md)。

## 实际结果

| 检查 | 结果 |
| --- | --- |
| Figure 2 样本 | 1600 个；原版和加速版均有 1599 个被作者算法判定为已求解 |
| Figure 2 两版对照 | 每个样本的求解状态、每 AP/总功率可行性、重试次数和外层迭代数全部一致 |
| Figure 3 时间对照 | 5 个随机种子，每个重复 5 次，交替运行顺序；各随机种子的加速比中位数再取中位数为 **8.90 倍** |
| Figure 3 累计求解时间 | 原版 71.27 秒；加速版 7.93 秒，共 25 次配对 |
| Figure 3 数值一致性 | 25 次配对的内外层迭代数均一致；最大目标值差 `2.52e-10 mW`，最终 AP 功率最大差 `4.71e-11 mW` |
| 自适应步长独立验证 | 30 个新场景，两版均成功 15 个；固定/自适应合计外层轮数 745/773、求解时间 47.14/48.32 秒；总体未改善 |
| 内层 Anderson 独立验证 | 另 30 个新场景，两版均成功 15 个；内层轮数 **3880→3019**，求解时间 **24.60→19.41 秒** |
| Anderson 重复计时 | 3 个非平凡场景各重复 3 次；相对现有缓存版的速度比中位数为 **1.25 倍** |
| 改变速率和簇大小 | 另 4 组、每组 12 个新场景；成功判定均一致，内层迭代与总时间每组均下降；两组无成功样本，不能用来主张可行率提高 |
| 等总连接数 AP 分配：新网络验证 | **60** 个此前未使用的网络、每个 100 次信道抽样、严格容差；固定每人 4 个 AP 成功 **31/60**，新分配成功 **41/60**，新增 10 个、失去 0 个 |
| 新分配的收益与代价 | 新增成功中的 9 个原方案被求解器判为不可行，1 个原方案未在预算内解出；成对成功率差 **+16.7 个百分点**，95% 网络重抽样区间 **+8.3 至 +26.7 个百分点**；总求解时间 **64.25→71.97 秒** |

这些时间来自一台 macOS arm64 机器、Python 3.12 和单线程 OpenBLAS；换机器可能不同。Figure 2 中速率为 4 bit/s/Hz 时，每 AP 功率约束下，本地 CSI 的可行比例为 0.18，集中式 CSI 为 0.43；总功率约束下分别为 0.31 和 0.83。比例按 **已求解的样本** 计算，与作者脚本一致；完整表格和 95% Wilson 区间见 [Figure 2 结果目录](results/figure2_full/)。

**为什么 seed 6 不可行？** Figure 3 的额外随机样本 seed 6 要求最低速率 3.5 bit/s/Hz。作者算法在第一次外层迭代得到约 `17,933.51 mW` 的对偶目标值，超过 16 个 AP 合计 `16,000 mW` 的功率上限，因此按作者程序的判定规则标记为“已求解但不可行”。当时报告的最大 SINR 缺口为 `1.0349`，最大单 AP 功率超限约 `2,046.53 mW`。原版和加速版对此一致；这反映该随机网络样本较难满足约束，而非加速版算错。Figure 3 原论文使用的是 seed 4，seed 6 是额外的稳健性检查。

## 尝试过但未采用的方案

- **自适应外层步长**：在 30 个新场景中没有改善总体成功数或总耗时，见 [实验记录](docs/ADAPTIVE_STEP.md)。
- **按 AP 服务人数选点**：50 个开发网络的成功数为原规则 30、新规则 29；未解出样本另行记录，见 [实验记录](docs/LOAD_AWARE_PILOT.md)。
- **按 AP 对偶价格选点**：6 个开发网络没有显示稳定收益，停止扩大试验，见 [实验记录](docs/PRICE_GUIDED_PILOT.md)。

## 图片和原始数据

- [Figure 2 完整曲线与抽样区间](results/figure2_full/figure2_with_ci.png)
- [Figure 3 原始对偶目标值曲线](results/figure3_official/dual_objective.png)
- [Figure 3 原始最大 AP 功率曲线](results/figure3_official/max_power.png)
- [25 次新版配对计时](results/figure3_repeats_cached/timings.csv)和[汇总](results/figure3_repeats_cached/summary.json)
- [复用前后独立配对](results/figure3_response_reuse/summary.json)
- [自适应步长逐场景对照图](results/adaptive_new_seeds/outer_iterations.png)和[全部原始记录](results/adaptive_new_seeds/runs.jsonl)
- [内层加速逐场景对照图](results/anderson_new_seeds/inner_iterations.png)、[完整配对数据](results/anderson_new_seeds/aggregate.json)和[重复计时](results/anderson_repeats/timings.csv)
- [不同计算时间预算下的描述性成功数](results/anderson_new_seeds/budget_success.png)
- [不同速率和簇大小的补充结果](results/anderson_robustness/aggregate.json)
- [等总连接数分配：60 网络成对结果图](results/variable_q_fresh_validation/paired_outcomes.png)、[逐网络结果与统计](results/variable_q_fresh_validation/summary.json)、[原始日志](results/variable_q_fresh_validation/runs.jsonl)
- [具体例子：同一网络 16 个 AP 的功率对照](results/variable_q_illustration_seed177/per_ap_power.png)
- [新分配在 3.0、3.5、4.0 目标速率的可行率曲线](results/variable_q_rate_sweep/feasibility_vs_rate.png)
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
python experiments/benchmark_repeats.py --output results/figure3_repeats_cached
python experiments/benchmark_response_reuse.py --output results/figure3_response_reuse
python experiments/benchmark_adaptive.py --output results/adaptive_new_seeds
python experiments/analyze_adaptive.py results/adaptive_new_seeds
python experiments/benchmark_anderson.py
python experiments/analyze_anderson.py results/anderson_new_seeds
python experiments/benchmark_anderson_repeats.py
python experiments/run_anderson_robustness.py
python experiments/analyze_compute_budget.py results/anderson_new_seeds
python experiments/analyze_anderson_effect.py results/anderson_new_seeds
python experiments/check_variable_q_equivalence.py
python experiments/compare_variable_q.py --seeds $(seq 166 225) --n-sim 100 --max-outer 120 --tol-fp 1e-5 --tol-psg 0.1 --output results/variable_q_fresh_validation
python experiments/analyze_variable_q.py results/variable_q_fresh_validation
```

Figure 2 的续跑程序逐个保存完成的样本，可以从已有记录继续。`results/` 内包含原始输出、配置、随机种子、失败或未收敛的案例及图表。

## 来源与许可证

作者代码注明 GPLv2；本仓库保留原有版权与许可证声明，并以 GPL-2.0-only 发布衍生代码，见 [LICENSE](LICENSE)。使用论文或代码开展研究时请引用[原论文](https://doi.org/10.1109/TSP.2024.3376809)。GitHub 的 Contributors 图通常只统计默认分支上的提交；作者的原始提交保存在 `upstream-baseline`，因此默认分支的图只显示本项目的提交者。这不改变作者代码的归属。
