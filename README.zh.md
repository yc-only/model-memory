# model-memory

[English](README.md)

给 AI Agent 用的模块记忆。模块的设计记忆放在对话之外：修改某个模块前，Agent 只加载这个模块的记忆；修改之后，把新的约定写回去。

Agent 在长周期开发中会忘记一个模块当初为什么这样设计。把整个项目装进上下文，又会把无关模块混在一起。压缩对话时，代码本身看不出来的决策也会丢掉。

model-memory 把这些决策保存在项目里：

- 用源码路径定位模块，不做语义搜索
- 只加载命中的那个模块
- 一轮任务结束时更新记忆，而不是每次编辑都写
- 更新记忆，不为了让记忆成立而修改代码

## 安装

```bash
npx skills add <owner>/model-memory
npx skills add <owner>/model-memory -a claude-code -y
npx skills add <owner>/model-memory -a cursor -y
npx skills add <owner>/model-memory -a codex -y
npx skills add <owner>/model-memory -a github-copilot -y
```

## Agent 如何使用

Skill 指示 Agent：

1. 把正在修改的源码路径对应到已登记的模块。
2. 读取该模块的 `memory.md`，再只读取需要的链接笔记。
3. 任务结束时记录已经落地的行为变化。

模块之间的依赖故意不记录，这部分直接从代码里看。

## 保存什么

记忆保存在仓库根目录的 `ModelMemorys/`：
项目根目录的 `ModelMemorys/`。项目根是当前工作目录；如果当前目录在项目内部，则向上使用已经存在的索引：

```text
ModelMemorys/
  model-link.json               # 模块名、一句话说明、源码目录
  <module-name>/
    memory.md                   # 简短入口：职责、接口、决策、已知问题
    content/                    # 一个主题一篇笔记，由 memory.md 链接
```
## 许可

[Apache License 2.0](LICENSE)
