# 模块对接协议 1.0

维护人：邹佩希。接口为 Python 和 UTF-8 JSON，正式 HTTP 路由交由系统成员封装；本地演示已有独立 HTTP 适配层，见 `docs/03_local_web.md`。所有时间单位为分钟；版本变动需更新 schema_version 与本说明。当前模型是离线条件模拟，不能包装为真实实时预测。

## 参数输入

完整可运行示例见 `examples/synthetic_config.json`。

| 字段 | 约束与含义 |
| --- | --- |
| schema_version | 固定字符串 1.0 |
| source_kind | synthetic / observed / literature / mixed |
| provenance | 非空，说明样本来源、日期范围、版本和假设；混合来源需在来源清单逐字段记录 |
| horizon_min | 大于零的有限数，到达窗口分钟数 |
| lockers | 非空数组；id 唯一字符串；capacity 和 pickup_servers 为正整数 |
| arrival_profiles | 每元素为一日/窗口的完整到柜轨迹数组，至少一条轨迹，空日用 []；不是一条订单代表一天 |
| 轨迹中的 id | 同一天唯一的匿名订单标识 |
| arrival_min | 到柜相对分钟，0 ≤ 值 < horizon_min；等于窗口终点的订单归下一窗口 |
| locker_id | 与 lockers.id 对应；没有自动路由或选址 |
| upstream_min | 可选，上游下单至到柜的总分钟数；缺失时 T1 字段为 null；可以使 T1 位于窗口开始前 |
| notice_delay_samples_min | 非空有限非负样本数组，入柜至通知 |
| walk_samples_min | 非空有限非负样本数组，通知至学生到柜 |
| pickup_service_samples_min | 非空有限正样本数组，扫码开柜等操作 |

不自动从原始 CSV 拟合参数；参数成员输出本配置。不同柜体/日期/天气分组的延迟如显著不同，应分场景提供；当前同一配置内各柜体共用样本池。缺失情境应返回缺失，不得静默降级晴天参数。`JsonParameterProvider` 以注册表精确匹配情境并校验配置。

## 调用

```python
from locker_model.adapters import JsonParameterProvider
from locker_model import predict, simulate, compare_capacities

provider = JsonParameterProvider('examples/registry.json')
config = provider.get_config('weekday_clear_lunch_normal')
result = predict(config, seed=42, replications=20)
trace_result = simulate(config, seed=42)
comparison = compare_capacities(config, [8, 16, 24], seed=42, replications=20)
```

在正常安装了 requirements 的虚拟环境中调用；本机 `.deps` 仅由 run.py 自动加载。种子为非负整数，重复次数 1—1000。容量对比使用相同种子及预先抽样输入，便于公平比较。多次运行会抽取整个到柜轨迹，并对各订单的延迟样本分别抽样，不保证模拟日期彼此独立于原数据。

## 返回与错误

`predict` 返回 schema_version、source_kind、provenance、seed、replications、metrics、run_mean_distribution、lockers、warnings。完整返回例见 `results/prediction.json`。`metrics` 的键为 deposit_wait_min、student_queue_wait_min、total_queue_wait_min、arrival_to_pickup_min，每项含 count、mean、p50、p90、p95、max。零订单时数值为 null，计数为 0；前端显示“无可用订单样本”，不能显示为零等待。

`lockers` 返回时间加权 utilization、full_time_fraction，均为 0—1。没有自动生成压力等级或“推荐最优容量”。`simulate` 另返回订单时刻和 `trace`；`trace` 的 occupied、delivery_queue、pickup_queue 分别为占用数、等柜位订单数、等待操作学生数，均不含正在操作的学生在 pickup_queue 内。

校验失败通常抛 ValueError；结构字段缺失可抛 KeyError，类型错误可抛 TypeError。后端统一转换为 400 INVALID_MODEL_INPUT；未知情境转为 422 SCENARIO_NOT_AVAILABLE；依赖或内部错误用 500 并内部记录，不向用户暴露路径与堆栈。HTTP 鉴权、计算配额、请求体大小和超时由系统成员负责，本模块只限制重复次数；还需限制订单量、柜体数与样本大小，以防服务阻塞。有效仿真结果 200，并原样展示来源和 warnings。

## 留出集评估接口

`locker_model.evaluation.evaluate(rows)` 接收同一等待口径的 actual_min、predicted_min、lower_min、upper_min，返回 n、mae_min、interval_coverage。样本必须来自未用于参数拟合的观测日期；此函数只做算术，不验证数据独立性。当前无真实验证集，只有评价函数的手算测试。反向下单预测、骑手配送链、最优选址等功能均无占位假结果，应在调用方标记未支持。
