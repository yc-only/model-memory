# model-memory

[中文](README.zh.md)

An Agent Skill that keeps module design memory outside the chat. Before changing a module, the agent loads only that module's memory. After the change, it checks whether the memory is still current.

Long-running agent sessions forget why a module was designed the way it is. Loading the whole project into context mixes unrelated modules together. Compressing the conversation drops the decisions that are not obvious from the code.

model-memory stores those decisions in the repository:

- one module is found by its source path, not by a semantic search
- only the matched module is loaded
- a file fingerprint shows whether the memory may be out of date
- the agent updates memory at the end of a task, not on every edit
- when memory and code disagree, it updates the memory after confirmation and does not change the code

## Install

```bash
npx skills add <owner>/model-memory
npx skills add <owner>/model-memory -a claude-code -y
npx skills add <owner>/model-memory -a cursor -y
npx skills add <owner>/model-memory -a codex -y
npx skills add <owner>/model-memory -a github-copilot -y
```

## How an agent uses it

The skill instructions tell the agent to:

1. Resolve the source path being changed to a registered module.
2. Load that module's `memory.md`, then only the linked notes it needs.
3. If the fingerprint changed, review the difference and update the memory after confirmation.
4. Record new responsibilities, interfaces, decisions, or known issues at the end of the task.

Module dependencies are intentionally not stored. Those come from reading the code.

## What is stored

Memory is stored in `ModelMemorys/` at the repository root:

```text
ModelMemorys/
  model-link.json               # module name, one-line description, source directories
  <module-name>/
    memory.md                   # short entry: responsibility, interfaces, decisions, known issues
    content/                    # one note per topic, linked from memory.md
    verification.txt            # generated fingerprint; do not edit
```

`config/fingerprint.yaml` chooses which files under a module's source directories participate in the fingerprint. Files in the memory directory are always included.

## License

[Apache License 2.0](LICENSE)
