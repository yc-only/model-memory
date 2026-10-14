---
name: model-memory
description: '模块记忆查询、校验与更新。Use when: 开始修改某模块代码前、需要了解模块设计意图或接口、完成一轮模块代码修改后。关键词：模块记忆、model memory、记忆校验、memory.md、ModelMemorys。'
argument-hint: '模块源码路径，或已登记模块名'
user-invocable: true
---

# 模块记忆

记忆在仓库根目录 `ModelMemorys/`。只加载本次路径命中的模块。

- 不记录跨模块依赖。
- 不修改源码。记忆与代码不一致时，只在用户确认后改记忆。
- 一轮任务结束时写一次记忆，不在每次编辑后写。

## 何时使用

- 修改已有模块代码之前。
- 要确认某模块的职责、对外接口、关键决策或已知问题。
- 一轮模块代码修改完成之后。

与已登记模块无关的问答，不跑本流程。

路径相对仓库根，用 `/`。命令里的 `python` 必须是 Python 3.6 及以上；不是时改用 `python3` 或 `py -3`，否则脚本直接以 `{"ok": false}` 退出。

## 阶段 1：任务开始

1. 确定要改的源码路径。路径不明时问用户，不猜模块。
2. 检索：

```powershell
python .agents/skills/model-memory/scripts/search_modules.py --query "<相对仓库根的源码路径>"
```

3. 只采用返回的 `matches`。已知模块名、但没有源码路径时，改用 `--name <module-name>`。路径未命中且返回 `name_hit` 时，改用该名字查询，不新建模块。
4. 逐个校验：

```powershell
python .agents/skills/model-memory/scripts/check_consistency.py --module "<module-name>"
```

- `TRUE`：读 `ModelMemorys/<name>/memory.md`，再按链接读取需要的 `content/`。
- `FALSE`：进入阶段 2。
- 无命中：不自动创建。

## 阶段 2：仅 FALSE 时校验

脚本只判断指纹是否变化。语义是否仍正确，由 Agent 判断。

1. 只核对输出中的 `added` / `removed` / `changed` 与 `warnings`，不通读模块。有 `warnings` 表示源码根未被跟踪，先修正 `source_roots`，不把 `FALSE` 当成正文过时。
2. 记忆仍然准确：不改正文，直接执行下方 `--write`。
3. 记忆已过时：列出差异，等用户确认。确认后先改完记忆正文，再执行 `--write`；用户拒绝则不改，且本轮不执行 `--write`。

记忆正文的修改本身也会改变指纹。先改完正文，最后只执行一次：

```powershell
python .agents/skills/model-memory/scripts/check_consistency.py --module "<module-name>" --write
```

看 `rewritten` 判断是否写入。`TRUE` / `FALSE` 只出现在不带 `--write` 的检查里。

## 阶段 3：一轮任务结束

1. 只记录职责、对外接口、关键决策、已知问题的变化。无行为变化的整理不记。
2. 没有相应记忆且值得记：先问用户。同意后按 [模块索引规范](./references/模块索引规范.md) 创建。
3. `desc` 或 `source_roots` 变化：用 `upsert_module.py` 更新，不手改 `model-link.json`。
4. 记忆正文按 [记忆编写原则](./references/记忆编写原则.md) 修改。`memory.md` 只写摘要。
5. 正文全部改完后，执行一次 `--write`。先写指纹再改正文，会使下次检查变成 `FALSE`。

## 禁止

- 不在每次编辑后更新记忆或指纹。
- 不在校验时改源码。
- 不手改 `verification.txt`。
- 不在记忆或索引中写跨模块依赖。
- 不把正文细节堆进 `memory.md`。

## 按需阅读

- 写正文：[记忆编写原则.md](./references/记忆编写原则.md)
- 核对指纹结论：[一致性校验规则.md](./references/一致性校验规则.md)
- 创建或更新模块：[模块索引规范.md](./references/模块索引规范.md)
