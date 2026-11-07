# 校园外卖柜优化建模与仿真

本项目面向校园外卖集中到达、柜位紧张和取餐时间难以预估的问题，采用数据处理、离散事件仿真与交互展示相结合的方式，研究等待时间及柜体容量配置。研究场景来自立项申请书，当前软件原型使用合成测试数据，尚未形成真实校园预测精度或实际配置收益结论。

## 分支与入口

| 分支 | 内容 | 使用方式 |
| --- | --- | --- |
| `main` | 团队公共介绍、架构、职责、数据与指标约定、协作流程 | 阅读及完善公共方案 |
| [`zpx/model-development`](https://github.com/changeable100/waiting_issue/tree/zpx/model-development) | 邹佩希的模型、网页演示、测试、合成实验、阶段报告和agent对接说明 | 在本机运行模型与演示 |

main目前是公共资料入口，不包含完整应用代码。访问 [开发分支使用说明](https://github.com/changeable100/waiting_issue/blob/zpx/model-development/README.md) 获取启动方法。

```powershell
git clone --branch zpx/model-development https://github.com/changeable100/waiting_issue.git
cd waiting_issue
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe web_server.py --open
```

需要Python 3.10或以上。浏览器访问 http://127.0.0.1:8765/，服务终端需保持运行。网页在本机调用Python模型，直接打开HTML文件不能运行仿真。

## 项目路线

数据采集 → 参数处理 → SimPy仿真 → 预测服务 → 网页或微信小程序展示 → 观测验证与优化分析。

到达轨迹和通知、步行、取餐操作样本作为模型输入，输出投递等待、学生取餐排队、到柜至取走延迟、占用轨迹、时间加权占用率和满柜时间占比。投递等待与学生排队分别记录，正式研究口径仍需评审确认。

## 当前进展

邹佩希开发分支已形成模型与本地网页原型，24项模型及HTTP测试通过，完成16类合成场景、3组容量、每组20次的960次仿真。提供四名成员的agent交接说明及逐步报告。上述结果只验证程序行为；真实数据校准、留出验证、正式系统集成与论文结论尚未完成。系统其他成员模块状态由各成员自行更新，不由本分支代报。

## 公共文档

- [项目目标与计划](docs/project/PROJECT_PLAN.md)
- [总体架构与模块接口](docs/project/ARCHITECTURE.md)
- [成员分工与协作](docs/project/COLLABORATION.md)
- [数据及指标约定](docs/project/DATA_AND_METRICS.md)
- [匿名观测字段模板](data/templates/observations_template.csv)

本仓库不包含原申请书中的学号、联系方式或其他个人资料；实测数据上传前需确认采集权限与匿名化处理。未选择项目开源许可证，仓库可见性不代表已授予通用开源许可。
