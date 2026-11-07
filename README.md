# 校园外卖柜模型开发

负责人：邹佩希。依据《校园外卖柜优化建模与仿真》立项申请书中的“模型构建与编程实现”分工，本仓库交付可独立运行的模型、参数对接接口、验证工具及逐步报告。具体子模块划分属于本次实施建议，尚未代替团队确认。原申请书未修改。

## GitHub分支

项目仓库为 [changeable100/waiting_issue](https://github.com/changeable100/waiting_issue)。`main` 维护团队公共介绍与方案，`zpx/model-development` 保存本人的开发内容。公共文档见 [main的项目文档](https://github.com/changeable100/waiting_issue/tree/main/docs/project)，分支与后续提交说明见 `docs/04_repository.md`。

```powershell
git clone --branch zpx/model-development https://github.com/changeable100/waiting_issue.git
```

## 开发步骤与当前状态

| 步骤 | 交付与验收 | 状态 |
| --- | --- | --- |
| 1 职责和指标 | 建立职责边界、时序和等待指标定义 | 已完成，见 reports/01_scope.md |
| 2 仿真模型 | SimPy 有限柜位、投递排队、通知步行、取餐操作、释放及轨迹 | 已完成，见 reports/02_model.md |
| 3 参数和服务接口 | 可替换情境配置、多次仿真、容量敏感性接口、误差评价接口 | 已完成，见 reports/03_interfaces.md |
| 4 工程验证和实验 | 手算案例、边界和守恒测试、16 类合成场景及 3 组容量 | 已完成，见 reports/04_validation.md |
| 5 本地网页演示 | 场景选择、容量调整、模型调用、曲线与统计、JSON导出 | 已完成，见 reports/05_local_web.md |
| 6 真实数据校准 | 接收团队数据、按日期划分训练集和验证集、校准与检验 | 待真实数据，未完成 |
| 7 团队联调和论文实验 | 与正式后端、优化及论文成员联调，确认口径，生成正式图表 | 待团队模块，未完成 |

## 打开演示界面

双击本目录 `Start_Demo.cmd`，将启动本机服务并打开浏览器。电脑需安装 Python 3.10 以上；本交付包已包含 SimPy 依赖。也可在本目录运行：

```powershell
python web_server.py --open
```

打开 [本地仿真实验台](http://127.0.0.1:8765/)。服务已启动时直接访问即可，不必重复启动；手动启动的终端需保持打开，按 Ctrl+C 可停止。若端口被其他程序占用，可用 `python web_server.py --port 8766 --open`。直接双击 HTML 文件不能运行模型。

页面支持16类情境、每柜1—200格、重复1—100次及随机种子。首次打开自动运行默认场景；条件修改后需点击运行，结果上方保留实际运行条件。卡片与分位数汇总多次仿真，占用曲线展示首轮轨迹。可导出完整运行JSON。

`web_server.py` 是仅监听127.0.0.1的本地演示适配层，不取代正式Flask服务与微信小程序。页面无外部字体、图表库或网络服务依赖。当前全部为合成数据，未接入真实预测或最优容量推荐。迁移见 `docs/03_local_web.md`。

## 运行

Python 3.10 以上。首次在本目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py test
.\.venv\Scripts\python.exe run.py demo
.\.venv\Scripts\python.exe run.py predict --config examples/synthetic_config.json --seed 42 --replications 20
```

本地交付环境已把 SimPy 4.1.1 安装到项目 `.deps`，`run.py` 会自动加载；GitHub不提交该依赖目录，其他电脑或从GitHub克隆后需按上述虚拟环境方式安装。依赖不写入用户系统环境。

`examples/` 是明确标记的合成数据；`prepare_examples.py` 可重建。`results/experiments.csv` 是便于 Excel 打开的实验表，`experiments.json` 包含分布和来源，`single_run.json` 包含逐订单记录与 Qk(t) 轨迹。重复执行使用相同种子，结果应一致。请勿把合成结果用于证明真实精度或真实扩容收益。

## 模型约定

所有时间为分钟，以所选观测窗口起点为 0；窗口限定订单到达时刻，运行会继续至所有订单取走。初始空柜；当前没有实时柜状态、弃单、错拿、超时清理、骑手批量配送或柜间转投。默认每订单一个格口，指定柜体不动态变化。取餐操作位用于表示扫码开柜等操作的并发限制，数量与服务时间仍需观测支持。

三项等待分别输出：`deposit_wait_min` 是骑手满柜投递等待；`student_queue_wait_min` 是学生到柜后的操作排队；`total_queue_wait_min` 为两者之和。总延迟 `arrival_to_pickup_min` 还包含通知、步行和取餐操作。新增的操作服务时间不能直接隐入申请书 tw。T2 定义为到柜时刻，入柜时刻单列；未给上游配送时长时，T1 相关字段返回 null。

占用率为到达窗口内占用格口数的时间积分除以容量和窗口长度；压力采用同窗口的满柜时间占比，不使用未经校准的“低中高”阈值。排队峰值包含窗口后排空期间；轨迹同一时刻可能有多个状态，积分按最后状态推进。按柜体分别统计，未假装完成布局优化。

结果中的 p50/p90/p95 是多次仿真订单的经验分位数；`run_mean_distribution` 是各次运行均值的分布。它们均不是统计置信区间，也没有完成真实预测区间校准。

## 对接与阶段检查材料

先阅读 [开发边界](docs/01_scope_and_plan.md) 与 [统一接口](docs/02_contract.md)。`docs/agents/` 中按成员分别准备了可以直接复制给 agent 的任务说明。`reports/` 中五份逐步报告对应五个已完成步骤，`reports/00_teacher_summary.md` 是阶段汇总。

仿真资源语义参考 [SimPy 官方共享资源说明](https://simpy.readthedocs.io/en/stable/simpy_intro/shared_resources.html)；依赖锁定为 4.1.1。未引用申请书里的未核验市场数字作为实验事实。
