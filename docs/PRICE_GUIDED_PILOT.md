# AP 对偶价格选点：小样本检验后停止

## 想法

原方法给每位用户选大尺度增益 `Gamma` 最大的 4 个 AP。我们先用 20 个信道样本运行原方法，读取求解器对每个 AP 功率约束形成的价格 `sig_l`，然后按 `Gamma_kl/sig_l` 重新给每位用户选 4 个 AP。价格越高，代表该 AP 的功率约束在当前求解中越紧。预期是把部分用户转向较不拥挤的 AP，从而改善满足约束的机会。价格只来自开发阶段的原规则求解；评测用相同网络几何、全新且两种方法共享的 40 个信道样本。

## 已运行的开发试验

种子 100–105，16 AP、16 UE、每 AP 4 天线、每 UE 4 个 AP、目标速率 3.5 bit/s/Hz、每 AP 1000 mW；每种方法最多尝试 `kappa=10,30`，每次最多 40 轮外层迭代。Python 3.12 环境下，六个网络的成功状态均一致：四对都找到可行解，一对双方未在预算内解出，一对双方被求解器判为不可行。种子 102 的新规则成功解的 AP 功率余量更接近零且耗时更长；种子 105 的新规则最终功率缺口远大于原规则。

此方法没有显示出稳定收益，因此停止扩大样本或调节价格指数，不把它作为成功改进。完整价格向量、簇、每次尝试、日志、时间和结果保存在 `results/price_guided_development/`；代码在 `price_guided_problem.py` 和 `experiments/compare_price_guided.py`。曾用本机较旧的 Python 3.8 环境做一次同配置探索，结果单独保存在 `results/price_guided_development_py38/`；正式叙述仅使用与论文复现实验一致的 Python 3.12 环境。

```sh
export OPENBLAS_NUM_THREADS=1 MPLCONFIGDIR=/tmp MPLBACKEND=Agg
python3 experiments/compare_price_guided.py --seeds 100 101 102 103 104 105 --eval-n-sim 40 --output results/price_guided_development
```
