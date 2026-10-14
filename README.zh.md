# model-memory

[English](README.md)

给 AI Agent 用的模块记忆。模块的设计记忆放在对话之外：修改某个模块前，Agent 只加载这个模块的记忆；修改之后，再检查这段记忆是否仍然有效。

Agent 在长周期开发中会忘记一个模块当初为什么这样设计。把整个项目装进上下文，又会把无关模块混在一起。压缩对话时，代码本身看不出来的决策也会丢掉。

model-memory 把这些决策保存在仓库里：

- 用源码路径定位模块，不做语义搜索
- 只加载命中的那个模块
- 用文件指纹提示记忆是否可能过期
- 一轮任务结束时更新记忆，而不是每次编辑都写
- 记忆与代码不一致时，经确认后修改记忆，不修改代码

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
3. 指纹发生变化时，核对差异，并在确认后更新记忆。
4. 任务结束时记录新增的职责、接口、决策或已知问题。

模块之间的依赖故意不记录，这部分直接从代码里看。

## 保存什么

记忆保存在仓库根目录的 `ModelMemorys/`：

```text
ModelMemorys/
  model-link.json               # 模块名、一句话说明、源码目录
  <module-name>/
    memory.md                   # 简短入口：职责、接口、决策、已知问题
    content/                    # 一个主题一篇笔记，由 memory.md 链接
    verification.txt            # 生成的指纹，不要手改
```

`config/fingerprint.yaml` 决定模块源码目录下哪些文件参与指纹。记忆目录中的文件始终参与。

## 许可

[Apache License 2.0](LICENSE)
