# 本地网页演示与迁移说明

本地演示由 `web/index.html`、`web/style.css`、`web/app.js` 和 `web_server.py` 构成。使用Python标准库HTTP服务，不新增Flask或前端构建依赖；仿真仍调用 `locker_model`，不在浏览器复制算法。

## 接口

GET `/api/scenarios` 返回scenarios数组，每项含id、label、source_kind，来源为现有registry.json。

POST `/api/simulate`，Content-Type为application/json，示例：

```json
{"scenario_id":"weekday_clear_lunch_normal","capacity":16,"replications":20,"seed":42}
```

成功返回settings、prediction、single_run。settings保留实际运行参数；prediction为现有predict输出；single_run为相同起始种子的simulate输出，含逐订单与状态轨迹。capacity对配置中各柜体同时生效，不代表增加柜体或优化分配。

输入范围：capacity为1—200整数，replications为1—100整数，seed为0—2147483647整数。只读取注册表中的配置；演示配置最多10柜、全部轨迹共10000单。请求体最多4096字节，同时只运行一个仿真请求。

| HTTP状态 | 含义 |
| --- | --- |
| 200 | 成功，保留来源标记 |
| 400 | JSON或参数无效 |
| 403 | Host或跨站Origin不允许 |
| 404 | 未知路由或文件 |
| 413 | 请求体过大或为空 |
| 415 | 非JSON请求 |
| 422 | 缺失场景参数 |
| 429 | 已有仿真运行 |
| 500 | 内部执行异常 |

静态文件只提供根页面、app.js和style.css，不开放项目目录。原生SVG绘制阶梯占用曲线，横轴为相对分钟，纵轴为占用格口；容量线与到达窗口终点单列。等待条形图按P90缩放并列出均值、P50、P95，不将经验分位数解释为置信区间。

## 启动与检查

双击 `Start_Demo.cmd` 或执行 `python web_server.py --open`，打开 http://127.0.0.1:8765/。先启动服务再访问，直接打开HTML无可用接口。仅使用本机回环地址，无公网部署、认证、多用户队列、持久化或生产部署。当前16场景均为synthetic；新增情境接入时需同步维护中文标签与选择控件。

`python run.py test` 包含24项模型和服务测试；HTTP测试使用临时端口并自动关闭，结果见 `results/web_test_log.txt`。JavaScript可用 `node --check web/app.js` 检查语法。浏览器检查默认加载、修改容量后重跑、非法值阻止提交和导出JSON。

## 后续成员集成

系统成员可保留页面并接入正式Flask路由，也可替换前端但保持模型协议；保留来源、局限与错误格式。演示结果不应保存到真实订单数据库。优化模块继续使用compare_capacities或自定义候选配置；界面不提供最优建议，防止把单次调参当作优化研究。

单轮轨迹与多轮指标有意分开，迁移后不要混成一个统计量。批量CSV实验仍由run.py demo输出；网页导出为含当前条件、统计及首轮轨迹的JSON。原有命令行流程继续可用。
