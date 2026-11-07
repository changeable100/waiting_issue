# GitHub仓库与分支说明

仓库：https://github.com/changeable100/waiting_issue

main只维护团队公共内容：项目介绍、目标计划、总体架构、成员职责、数据与指标约定、匿名观测模板。邹佩希的代码与开发材料位于zpx/model-development，该分支从main创建并保留公共文档。其他成员可直接访问分支阅读代码、下载或克隆；可见范围以仓库本身的GitHub权限为准，本次未更改仓库可见性或成员权限。

## 开发分支内容

包含locker_model、web、tests、examples、results中的合成实验与测试证据、reports、docs中的接口及agent说明、启动脚本和requirements.txt。不会提交本地依赖、虚拟环境、缓存、进程ID、服务运行日志、凭据或原申请书。GitHub克隆后需自行安装requirements.txt。

## 本机工作目录

本次Git工作副本是 `D:\Waiting\waiting_issue`，开发材料原目录 `D:\Waiting\campus-locker-zpx` 保留。两者是独立副本，不会自动同步。后续建议在Git工作副本的zpx/model-development分支直接开发并提交；若在原目录修改，应确认需要同步的文件后复制到工作副本，检查差异再提交，不能直接在原目录运行git push。

```powershell
cd D:\Waiting\waiting_issue
git switch zpx/model-development
git status
git diff
# 确认改动并执行相关验证后，选择具体文件暂存
git add <文件路径>
git commit -m "说明本次改动"
git push origin zpx/model-development
```

不要强制推送main或其他成员分支。公共文档修改应单独提交到main；个人开发分支按需合并main，遇到README冲突保留个人启动说明与公共文档入口。跨模块指标或协议变更需同步维护接口说明和相关成员文档。
