# Agentic Statistical Analysis Assistant

Local course MVP: CSV + natural-language question → DeepSeek Planner → deterministic method/checks → SciPy → DeepSeek Interpreter → bounded review. Implemented with an actual LangGraph StateGraph. Supports independent Welch comparisons, Pearson correlation, categorical chi-square independence and simple OLS with one predictor and intercept.

**Quick start (Python 3.12):** create a virtual environment, install `requirements-lock.txt`, then run `python ui_server.py --port 8766` and open http://127.0.0.1:8766/ . The UI is English-only. Default offline mode uses fixed test doubles; select DeepSeek for real model calls. Configure `DEEPSEEK_API_KEY` in a local `.env` using the blank `.env.example`, never in committed files.

**Examples and tests:** [test case guide](docs/TEST_CASES.md), [student live walkthrough](docs/STUDENT_DEMO.md), [evaluation and limitations](docs/EVALUATION.md). Run `python -m pytest -q` for automated tests. The current [self-contained submission notebook](deliverables/LangGraph_Submission.ipynb) contains saved live outputs and the [actual graph image](deliverables/graph.png). It embeds the implementation and synthetic data; no supporting project files are needed.

Model outputs are not guaranteed statistically or semantically correct. Code supplies numerical values; partial text checks may withhold explanations. Memory is in-process only. This repository is a local application, not a hosted web service.

本地课程 MVP：CSV + 自然语言问题 → Planner → 方法规则 → 数据诊断 → SciPy → Interpreter → 解释检查。暂停询问用户，计划最多修订一次，解释最多重写一次。不能合理分析时明确停止。

当前范围：独立两组 Welch t-test、Pearson correlation、分类变量 chi-square independence、单预测变量 OLS regression。配对、聚类、重复测量、多元/逻辑回归和自动替代检验均不支持。所有输出保守地限制为关联或组间差异，不作因果结论。LLM 不生成可执行 Python。

## 本地运行

### 浏览器界面（推荐）

现有环境已安装，无需重新安装依赖。在项目目录运行：

```powershell
.\.venv\Scripts\python.exe ui_server.py --port 8766
```

浏览器打开 http://127.0.0.1:8766 。全英文界面，内置两组比较、相关分析及配对设计停止案例。选择案例 → Run analysis → 确认独立/配对等设计 → Confirm & continue。相关分析完成后可点击明确的 2025 日期窗口按钮，观察 n 从 20 变成 10。也可上传 CSV 并输入问题。

默认 Offline demonstration 使用固定替身；选择 DeepSeek 才调用真实模型。离线替身只支持固定演示逻辑，不适合检验任意自然语言。界面与模型解释均使用英文。上传内容不写入文件，服务仅监听本机；重启清除所有会话。计算结果及审查失败均可查看，未通过审查的解释会隐藏。

Python 3.12 推荐。在此目录：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe demo.py
.\.venv\Scripts\python.exe -m pytest -q
```

默认 demo 是 **offline test double**：真实 LangGraph + 真实 SciPy，Planner/Interpreter 是固定演示替身，不是 LLM。不能据此声称完成真实多 agent 或自然语言准确率评估。

DeepSeek 模式：把 `.env.example` 复制为 `.env`，仅在本地填入密钥；或配置 `DEEPSEEK_API_KEY` 环境变量。默认模型 `deepseek-chat`。然后运行：

```powershell
.\.venv\Scripts\python.exe demo.py --live
```

也可分析自己的 CSV：

```powershell
.\.venv\Scripts\python.exe demo.py --live --csv examples/trial.csv --question "Compare outcome between treatment and control"
```

先确认输入的是可用于课程演示的数据。模型只接收列概况、结构化计划和统计摘要，不接收完整 CSV；列名、分类标签、用户问题仍会发给 API。每个分析最多五次模型请求，每次超时 45 秒，没有网络自动重试。日志不存密钥。用户明确指定 CSV 的输出可能包含列名/分组标签，默认不落盘；`artifacts/` 的默认演示只使用虚构数据。

## 如何看演示

- `demo.ipynb`：步骤、暂停/恢复、同会话追问、停止场景。
- `artifacts/demo_results.json`：虚构数据的结构化结果与节点轨迹。
- `artifacts/graph.mmd`：从 compiled graph 导出的 Mermaid。
- `artifacts/graph.png`：从同一个 graph 的 `draw_mermaid_png()` 导出（需要网络）。

notebook 中请选择本项目 `.venv` 的 Python 内核。内存 checkpointer 使用 thread_id 隔离会话，程序重启后消失，不是长期记忆。追问重用变量/意图，所有子集诊断和统计重新计算。日期筛选使用明确的 start/end；“最近一年”有歧义时问用户。

## 检查政策与局限

有效样本、类型、缺失、无穷值、常量、组数为代码检查；独立性必须由用户确认。Shapiro、偏度、IQR 离群计数作为诊断，不把 p<0.05 自动转换为另一检验。每组至少五条、Pearson 至少四对，是 MVP 的保守服务政策，不是统计学普适门槛。小组样本不足三十且严重偏态/极端离群时停止，请求人工判断。拒绝自动删除离群值。

Welch 输出第二个排序组减第一个排序组的原始均值差及区间；Pearson 输出 r 及 Fisher 变换区间。按分析涉及的列完整案例处理缺失，报告删除数量；不保证缺失机制无偏。Pearson 的默认推断前提可能不满足；提供分布、异常值警告，不能声称代码自动验证线性、独立性或研究设计。

解释模型使用占位符，数字由代码填入；结构、保守因果政策、规定限制、结论强度和部分危险表述受检查。语义检查是有限启发式，不能保证文字完全无误。未通过重写的解释不展示，仍保留可信数字。相关或 t-test 都不能单凭 p 值证明/否定因果、无效或实际重要性。

## 老师要求映射

plan 输出与方法理由在 notebook 中展示；diagnostics 展示实际检查；revisions/rewrites 各上限一；追问实例复用计划而重新计算；tests 覆盖边界和解释拒绝。测试用例不是真实 LLM benchmark；已有真实调用与实际错误记录；独立人工语义审核仍未完成。五页英文 PPT 和两页英文 writeup 已制作，位于 `deliverables/`；个人网站 lab/writing 尚未发布，GitHub 已建立。


## 真实案例评估

`benchmark.py` 用固定随机种子的十二个虚构数据案例验证两种方法、角色映射、追问、异常停止、缺失处理及非线性边界。运行会调用真实 DeepSeek；逐例保存，不需要手动逐条提交。

```powershell
.\.venv\Scripts\python.exe benchmark.py
```

原始评估在 `artifacts/benchmark_live.json` / `benchmark_report.md`，定向复测在 `benchmark_recheck_live.json` / `benchmark_recheck_report.md`。请保留基线与复测的区别，不把三例复测通过写成全套重新通过。解释语义仍需要组员独立审核。

## Four-method cases and current evaluation

See [benchmark v2 guide](docs/BENCHMARK_V2.md). Thirty-one synthetic cases are separated into [normal](examples/benchmark_v2/normal), [boundary](examples/benchmark_v2/boundary), [clarification](examples/benchmark_v2/clarification), [stop](examples/benchmark_v2/stop), and [followup](examples/benchmark_v2/followup). Each CSV has a labelled JSON with its question, metadata, expected behavior and numerical reference where applicable.

Run `python benchmark_suite.py --mode offline --output my_offline_run` for gold-plan mechanics or `--mode live --output my_live_run` for DeepSeek. Choose a fresh output name; historical results are preserved. [Initial live v2 report](artifacts/benchmark_v2/live_v2_first/REPORT.md): strict mechanical checks 28/31; all 17 computed results matched reference numbers and passed partial explanation checks. Three safe route/goal deviations are documented. This is not a semantic reliability percentage.

[Interpretation challenge set](examples/interpretation_checks/REPORT.md): controlled valid templates plus deliberately planted mistakes. Code caught nine of twelve planted errors and accepted four valid templates; misses demonstrate limitations. Run `python interpretation_benchmark.py`. No AI Reviewer or required human approval node has been added.

Chi-square uses named categorical labels, Pearson statistic without Yates correction, and an explicit expected-count approximation policy. It reports Cramer's V without an effect interval. Simple OLS reports slope, intercept, R-squared, slope interval and residual diagnostics. Heteroscedasticity/influence warnings do not trigger silent estimator changes. [SciPy chi-square](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.chi2_contingency.html) and [linregress](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.linregress.html) describe the underlying calculations.

`submission/` remains the historical executed two-method package; `demo.ipynb` is the current four-method teaching notebook with explicitly offline default.

## Current visualization package

Use `assignments/2026-10-12/langgraph/LangGraph_Submission.ipynb` and `assignments/2026-10-12/langgraph/graph.png` for the current graph submission. `LangGraph_Visualization_Current.zip` now contains exactly those two files; the short node/edge/handoff explanation is below the image inside the notebook. The self-contained notebook was executed with real DeepSeek calls from an empty working directory. `submission/` and `submission_current/` retain older packages. Midterm deliverables are `assignments/2026-10-12/midterm/Midterm_Presentation_Final.pptx` (five slides with five-minute speaker notes) and `assignments/2026-10-12/midterm/Midterm_Writeup.docx` / `.pdf` (two pages). Built-in cases include selection guidance, expected behavior, suggested follow-ups and a U-shaped Pearson boundary example.

## Public deployment preparation

[Public service status](docs/PUBLIC_SERVICE_STATUS.md) describes the isolated Docker release, privacy limits, persistent quotas and cost ceilings. Run `deploy/build-release.ps1` to test and package a local release. CI checks every push; release publication is manual. No server deployment or website Lab link is active yet. Shared Caddy integration requires a separate review before installation.
