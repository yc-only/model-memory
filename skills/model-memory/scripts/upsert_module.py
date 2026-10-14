# -*- coding: utf-8 -*-
"""Create or update a module index entry and its memory skeleton.

Usage:
    python upsert_module.py --name foo --desc "一句话" --source-root Assets/Path/To/Foo
    python upsert_module.py --name foo --desc "新的一句话"
    python upsert_module.py --name foo --remove
"""

import argparse
import os
import shutil

import _common as common

MEMORY_TEMPLATE = """# {name}

## 职责
待补充。

## 对外接口
- 待补充。

## 关键决策
- 待补充。

## 已知问题
- 待补充。

## 置信状态
- 当前：low
- 上次校验：未校验
"""


def create_skeleton(name):
    directory = common.memory_dir(name)
    os.makedirs(os.path.join(directory, "content"), exist_ok=True)
    memory_path = os.path.join(directory, "memory.md")
    if not os.path.exists(memory_path):
        with open(memory_path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(MEMORY_TEMPLATE.format(name=name))


def upsert(args):
    name = common.validate_name(args.name)
    index = common.load_index(create=True)
    existing = common.find_model(index, name)

    if args.remove:
        if existing is None:
            raise common.MemoryError("索引中不存在模块：%s" % name)
        index["models"] = [item for item in index["models"] if item.get("name") != name]
        common.save_index(index)
        return {"ok": True, "action": "removed", "module": name, "memory_kept": True}

    if existing is None:
        if not args.desc or not args.source_root:
            raise common.MemoryError("新建模块必须同时提供 --desc 与至少一个 --source-root")
        roots = [common.norm_rel(root) for root in args.source_root]
        for root in roots:
            common.require_source_dir(root)
        entry = {
            "name": name,
            "desc": args.desc.strip(),
            "source_roots": roots,
            "memory_path": "./%s" % name,
        }
        directory = common.memory_dir(name)
        existed = os.path.isdir(directory)
        create_skeleton(name)
        try:
            entries, warnings = common.fingerprint_entries(entry)
            if warnings:
                raise common.MemoryError("；".join(warnings))
            index["models"].append(entry)
            common.save_index(index)
            digest = common.write_verification(directory, entries)
        except Exception:
            saved = common.find_model(common.load_index(), name) is not None
            if not existed and not saved:
                shutil.rmtree(directory, ignore_errors=True)
            raise
        return {"ok": True, "action": "created", "module": entry, "verification": digest}

    if args.desc:
        existing["desc"] = args.desc.strip()
    if args.source_root:
        roots = [common.norm_rel(root) for root in args.source_root]
        for root in roots:
            common.require_source_dir(root)
        existing["source_roots"] = roots
    if not args.desc and not args.source_root:
        raise common.MemoryError("更新时至少提供 --desc 或 --source-root")
    common.save_index(index)
    return {"ok": True, "action": "updated", "module": existing, "verification_rewritten": False}


def main():
    parser = argparse.ArgumentParser(description="创建或更新模块记忆元数据")
    parser.add_argument("--name", required=True, help="模块名，同时作为目录名")
    parser.add_argument("--desc", help="一句话模块简介")
    parser.add_argument("--source-root", action="append", help="源码根目录，可重复；提供则整体替换")
    parser.add_argument("--remove", action="store_true", help="只从索引移除，不删除记忆目录")
    args = parser.parse_args()
    try:
        common.emit(upsert(args))
    except common.MemoryError as exc:
        common.fail(str(exc))


if __name__ == "__main__":
    main()
