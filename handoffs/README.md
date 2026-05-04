# handoffs/

> 本目录存放**已完成 phase** 的交接文档，由 CLAUDE.md「Project Principles」第 6 条强制要求。
>
> 目的：让一个**没有当前会话上下文**的新 Claude 实例读完即可接手，不依赖任何口头说明。

## 命名规范

```
handoffs/<YYYY-MM-DD>-<phase-id>-handoff.md
```

- `YYYY-MM-DD`：phase 收口日期（不是开始日期）。
- `phase-id`：与 `plans/<topic>-phases.md` 中的 phase id 完全一致（如 `pixel-phase-0`、`pixel-phase-1`）。
- 一个 phase 一份 handoff。返工/重启不创建新文件，在原 handoff 末尾追加「补遗」小节。

示例：
```
handoffs/2026-05-10-pixel-phase-0-handoff.md
handoffs/2026-05-12-pixel-phase-1-handoff.md
```

## 必填小节（顺序固定）

每份 handoff **必须**包含以下 5 节，缺一不可：

### 1. 背景
这个 phase 要解决什么问题？上游约束是什么？指向所属 plan 文档与上一个 handoff（首个 phase 除外）。

### 2. 目标
原计划承诺要交付什么？复制 / 链接 `plans/<topic>-phases.md` 对应行的「交付」与「验收」字段。

### 3. 当前进度
checklist 形式列出所有交付项：
- `[x]` 已完成
- `[~]` 进行中（注明完成度与阻塞）
- `[ ]` 未开始

### 4. 完成情况
- 实际交付物（路径 + 简述）
- 关键决策与权衡（**为什么**这么做）
- 偏离原计划的地方及原因
- 触发的 CLAUDE.md 原则冲突或例外申请

### 5. 后续任务
- 下一个 phase 的入口与目标
- 已知风险、未决问题
- **新会话立刻要读哪些文件**（路径列表，按阅读顺序）
- 推荐的第一条命令（验证当前状态完好）

## 反模式（禁止）

- 用 git log 或 PR 描述代替 handoff——那些是「做了什么」的记录，不是「下一步做什么」的指南。
- 写「详见聊天记录」「问 Hugh」——必须自包含。
- 只贴代码片段不写决策原因——CLAUDE.md 第 4 条 ETC 要求未来可改，决策原因比代码本身更重要。
- 静默跳过「偏离原计划」一节——没偏离就明确写「无偏离」。

## 与 plans/ 的回链

每份 handoff 写完后，到对应 `plans/<topic>-phases.md` 的该 phase 行追加 handoff 链接，形成双向索引。
