# plans/

> 本目录存放**前瞻性**的设计与拆解文档：phase 拆分、技术方案、内容包计划等。
>
> 与 `handoffs/` 的区别：`plans/` 描述**还没做**或**正在做**的事；`handoffs/` 描述**已经做完**的 phase 状态。

## 目录约定

- **命名**：`<topic>-plan.md`、`<topic>-phases.md`、`<topic>-design.md`。topic 用 kebab-case，全小写。
- **来源**：长篇外部计划（如来自笔记仓库）允许只在本目录放索引/拆解，并在文档顶部链接到外部源文件路径，避免重复。
- **生命周期**：plan 落地完成后**不删除**，加 `> 状态：已完成（→ 见 handoffs/...）` 标注，保留为历史依据。
- **修订**：plan 修改超过结构性范围时，必须在「变更记录」小节追加一行（日期 + 改了什么 + 原因），便于后续会话理解为什么和源 plan 不一致。

## 当前文档

| 文件 | 用途 | 状态 |
|---|---|---|
| `pixel-phases.md` | 像素化改造（Phase 0-7）拆解索引 | 进行中 |

## 与 CLAUDE.md 第 6 条的关系

CLAUDE.md「Project Principles」第 6 条规定每个 phase 完成后必须写 handoff 文档。本目录下的 `*-phases.md` 即是 handoff 文档的**索引父表**：

- 拆解所有 phase 的范围、交付、验收
- 每个 phase 完成后，在对应行追加 handoff 文档链接

新 Claude 会话接手时的标准入口顺序：

1. 读 `CLAUDE.md`
2. 读 `plans/<topic>-phases.md` 找当前 phase
3. 读 `handoffs/` 下最新一份 handoff 拿到精确进度
