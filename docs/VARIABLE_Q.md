# 等总 CSI 连接数的自适应 AP 分配

## 为什么值得试

原论文的本地 CSI 设置让每位用户都连接大尺度增益最大的 4 个 AP。对所有用户一律分配 4 条连接很简单，但弱用户可能需要更多 AP 协作，强用户则可能用较少 AP 就能达到同样的最低速率。我们的研究问题是：**总共仍只估计 64 条 AP–用户信道时，按用户的长期信道条件重新分配连接，能否让更多网络同时满足每个 AP 的功率上限和所有用户的最低速率？**

规则在独立验证前固定：按每位用户最强 4 个 AP 的大尺度增益之和排序；最弱 4 人各连接其最强的 6 个 AP，中间 8 人各连接最强的 4 个，最强 4 人各连接最强的 2 个。总连接数仍是 `4×6+8×4+4×2=64`。这不是增加 AP 数量或发射功率，也没有用评测信道样本挑选连接。实现见 `variable_q_problem.py`。原论文的模型、每 AP 功率/SINR 约束与求解器其余部分保持一致；为了支持不同长度的用户簇，局部波束成形方程按每个用户的簇大小建立。`experiments/check_variable_q_equivalence.py` 检查把新代码强制设回每人 4 个 AP 时，与原缓存版的波束成形参数和信道系数一致，已在 3 个种子通过。

## 公平比较与判定

每对方法使用相同网络几何、阴影衰落、瞬时信道实现、目标速率、16 个 AP、16 位用户、每 AP 4 根天线、每 AP 1000 mW 上限、**合计 64 条 CSI 连接**，并交替运行顺序。每个网络做 100 次信道抽样；每种方法最多尝试 `kappa=10,30`，每次最多 120 轮外层迭代；内层容差 `1e-5`，AP 功率容差 `0.1 mW`。成功须由同一求解器报告可行。失败再区分为求解器的不可行判定和达到迭代上限的未解出，后者不能当作物理不可行。最终报告的 SINR 缺口和 AP 功率缺口也逐样本保存。方法的总 CSI 连接数相同，**单个用户得到的连接数不同**；每 AP 的 CSI 负担和协调方式未被强制相同，这是比较边界。

## 开发与验证结果

低成本开发试验（种子 100–111、20 次信道抽样、较宽容差）为固定 8/12、新方案 10/12；新增 2 个都是原方案在外层预算内未解出，不能作为无线可行域扩大的证据。全部原始记录在 `results/variable_q_development/`。

随后保持规则不变，在种子 136–165 上用严格参数重跑：固定方案 **18/30**、新方案 **20/30**；新增的种子 136、137 原方案触发求解器不可行判定，新方案满足功率/SINR 阈值，0 个反向案例。总求解时间为 **32.01→35.86 秒**。先前较宽容差、较短预算的试跑也保留在 `results/variable_q_holdout/`；严格结果在 `results/variable_q_strict/`，不混算两批。

最后用此前未查看过的 **60 个新网络（种子 166–225）**、完全相同的严格规则和参数独立验证：

| 指标 | 固定每人 4 个 AP | 等总连接数的可变分配 |
| --- | ---: | ---: |
| 找到满足约束的解 | **31/60** | **41/60** |
| 求解器判为不可行 | 28 | 17 |
| 达到迭代预算、未解出 | 1 | 2 |
| 总求解时间 | 64.25 秒 | 71.97 秒 |
| 成功样本最大报告 SINR 缺口 | 0.0001 | 0.0001 |

逐网络看，新方案新增成功 **10** 个、失去成功 **0** 个。新增的 10 个中，原方案 9 个被求解器判为不可行，1 个（种子 190）只是达到迭代上限；因此最稳妥的无线结论是**至少有 9 个明确的求解器判定转换**，总预算内成功率提高 10/60，即 **16.7 个百分点**。以网络为单位成对重抽样，差值的 95% 百分位区间为 **8.3–26.7 个百分点**；10 个不一致配对的双侧精确 McNemar 检验 `p=0.00195`。这是对该网络生成分布和仿真设置的统计证据，不是所有网络必然改善的定理。求解总时间增加约 **12.0%**，因此这项方法主张的是**约束可行率**，不主张计算提速；求解时间也是单次计时，不能当作稳定硬件加速结果。

具体例子：种子 137 中，固定 4 个 AP 的最终对偶目标约 `16,238.75 mW`，超过 16 个 AP 合计 `16,000 mW` 上限，按作者程序判为不可行；可变分配的最终最大 AP 功率缺口是 `-1.30 mW`，即每个 AP 均低于上限。两种方法对同一随机网络、同一信道实现求解。完整逐样本结果、全部外层日志、参数、种子、图见 `results/variable_q_fresh_validation/` 和 `results/variable_q_strict/`。

更直观的[种子 177 的 16 个 AP 功率图](../results/variable_q_illustration_seed177/per_ap_power.png)显示：固定分配时求解器最终迭代的若干 AP 超过 `1000 mW`，可变分配找到的解每个 AP 均在上限内。图中的固定分配柱子是**被判为不可行的求解器最终迭代**，不能解释成固定分配的可行设计；逐 AP 数值、连接列表和完整日志在 `results/variable_q_illustration_seed177/data.json`。这个例子是在看到验证结果后选作说明，不参与成功率统计之外的额外推断。

## 其他速率与限制

对新的种子 226–245，在**同一批 20 个网络**上用相同严格参数测试三个目标速率。结果如下；完整三点可行率曲线见 `results/variable_q_rate_sweep/feasibility_vs_rate.png`，原始记录分存在 `results/variable_q_rate_stress/` 和 `results/variable_q_rate_middle/`。

| 最低速率 (bit/s/Hz) | 固定 4 个 AP | 可变分配 | 新增 / 失去成功 |
| --- | ---: | ---: | ---: |
| 3.0 | 18/20 | 18/20 | 0 / 0 |
| 3.5 | 12/20 | 13/20 | 1 / 0；原方案未在预算内解出 |
| 4.0 | 6/20 | 8/20 | 2 / 0；原方案被判为不可行 |

同一网络在三个速率下重复出现，因此不能把这 60 行当作 60 个独立网络进行总体显著性检验。这个补充样本较小，单独看不能证明各速率都改善；它显示了低速率时的相同结果和较高目标下的潜在收益。

这些结果仅覆盖论文的本地 CSI、16 AP/16 UE、特定路径损耗模型及所设 64 条连接预算。`N_sim=100` 是 Monte Carlo 近似；其他系统规模、信道模型、目标速率和每 AP CSI 上限仍需实测。多用户之间的 CSI 连接数重新分配是资源取舍；不应声称速率上限或所有场景的性能都提升。

## 复现命令

```sh
export OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg MPLCONFIGDIR=/tmp
python3 experiments/check_variable_q_equivalence.py
python3 experiments/compare_variable_q.py --seeds $(seq 136 165) --n-sim 100 --max-outer 120 --tol-fp 1e-5 --tol-psg 0.1 --output results/variable_q_strict
python3 experiments/analyze_variable_q.py results/variable_q_strict
python3 experiments/compare_variable_q.py --seeds $(seq 166 225) --n-sim 100 --max-outer 120 --tol-fp 1e-5 --tol-psg 0.1 --output results/variable_q_fresh_validation
python3 experiments/analyze_variable_q.py results/variable_q_fresh_validation
python3 experiments/compare_variable_q.py --seeds $(seq 226 245) --rates 3.0 4.0 --n-sim 100 --max-outer 120 --tol-fp 1e-5 --tol-psg 0.1 --output results/variable_q_rate_stress
python3 experiments/analyze_variable_q.py results/variable_q_rate_stress
python3 experiments/compare_variable_q.py --seeds $(seq 226 245) --rates 3.5 --n-sim 100 --max-outer 120 --tol-fp 1e-5 --tol-psg 0.1 --output results/variable_q_rate_middle
python3 experiments/analyze_variable_q.py results/variable_q_rate_middle
python3 experiments/combine_variable_q_rate_sweep.py
python3 experiments/analyze_variable_q.py results/variable_q_rate_sweep
python3 experiments/illustrate_variable_q.py
```
