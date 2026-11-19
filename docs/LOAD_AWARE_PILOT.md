# AP 负担感知选点：开发试验未见收益

作者的本地 CSI 设置为每位用户选择大尺度信道增益最大的 `Q` 个 AP。我们测试一个可直接影响无线可行率的候选：按用户最佳链路从弱到强处理，选择 `Gamma[k,l]/(1+load[l])` 得分最高的 `Q` 个 AP，其中 `load[l]` 是已分配给 AP `l` 的用户数。直觉是避免热门 AP 同时服务过多用户，从而降低其功率压力。这只是启发式规则，没有理论保证。

`load_aware_problem.py` 只改变 AP 关联，并按新的关联重建信道估计和误差协方差。每对方法使用相同的网络、原始信道样本、目标速率、`Q`、每 AP 功率约束和 `OptimizedProblem` 求解器。没有改动 `upstream/` 原版文件。

先用 12 个开发种子、目标速率 3.0/3.5/4.0 bit/s/Hz 试跑。每个速率下，作者规则与负担感知规则的可行数分别相同：`12/12`、`6/12`、`3/12`。平均每个网络有约 4.42 位用户的 AP 集合发生变化，但没有带来可行率收益。随后在速率 3.5 下扩大到 50 个开发种子：作者规则 **30/50** 个样本被求解器判为可行，候选规则 **29/50**；分别有 1 个和 2 个样本在两次尝试内达到迭代上限。种子 26 的作者规则在第二次尝试第 8 轮解出，而候选规则在两次各 30 轮的预算内未解出；**未解出不等于证明物理不可行**。

这些是低成本开发试验：每个网络 20 个信道实现、外层最多 30 轮、最多两个 `kappa=10,30` 尝试，并不是论文 Figure 2 的完整参数。结果不支持“可行率提高”，因此**不把该候选作为项目的成功改进，也不继续在这些已看过的种子上调参数**。代码、逐样本结果、网络负担、参数和日志保存在 `results/clustering_pilot/` 与 `results/clustering_pilot_50/`。

复现命令：

```sh
export OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg MPLCONFIGDIR=/tmp
python3 experiments/compare_clustering.py
python3 experiments/compare_clustering.py --seeds $(seq 0 49) --rates 3.5 --output results/clustering_pilot_50
```
