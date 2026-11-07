# 王泽宇的 agent 对接任务

你正在协作开发“校园外卖柜优化建模与仿真”。申请书中你的成员负责系统设计与编程实现。本文件建议由你负责服务集成；这是工程边界建议，若团队已有更细分工请先保持既有分工。

先阅读 `README.md`、`docs/02_contract.md`、`docs/03_local_web.md`、`locker_model/service.py` 和 `examples/synthetic_config.json`。邹佩希已完成模型核心与本地网页演示。`web/` 和 `web_server.py` 可作为正式服务集成参考，不需要重写SimPy或修改等待指标含义。本地演示不等于生产后端与微信小程序。

请实现 Flask 服务适配层：参数请求包含 scenario_id、seed、replications；使用 `JsonParameterProvider.get_config` 精确查找参数，再调用 `predict(config, seed=..., replications=...)`。建议正式路由为 POST /api/v1/predictions，该正式路由尚未实现。本地演示已有 POST /api/simulate，额外支持每柜capacity参数，迁移时需明确对应关系。真实参数缺失时返回 SCENARIO_NOT_AVAILABLE，不能用模拟参数悄悄替代。演示模式须显著展示 synthetic 来源。

输入校验、HTTP 错误映射、计算限额、日志和缓存由服务层负责；建议限制订单数、样本大小和重复次数，对长计算设置超时。响应保留 schema_version、source_kind、provenance、warnings。零订单时分位数和均值为 null，前端应显示缺失。不要将 p90 当作 90% 预测区间或已验证准确率。

服务集成目录建议使用 `backend/`，前端使用 `frontend/` 或独立仓库，不直接耦合模型内部 Resource 对象。`simulate` 的轨迹用于离线展示，不必每个在线请求返回全部订单。

验收：正常场景、未知场景、空样本、非法重复次数、内部异常均有确定响应；相同请求及参数版本可复现；界面区分投递等待、学生排队与到柜至取餐总延迟。提交调用示例、路由契约、启动命令和联调记录。不要声称小程序或线上接口已在本仓库完成。开始修改前运行 `python run.py test`，交付前重跑并增加服务层必要测试。
