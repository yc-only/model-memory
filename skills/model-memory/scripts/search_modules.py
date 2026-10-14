# -*- coding: utf-8 -*-
"""Resolve a source path to the most specific registered memory module.

Usage:
    python search_modules.py --query Assets/GameLogic/Scripts/UI/Foo/Bar.cs
"""

import argparse

import _common as common


def model_by_name(index, query):
    wanted = query.strip().lower()
    for model in index["models"]:
        if isinstance(model, dict) and str(model.get("name") or "").lower() == wanted:
            return model
    return None


def describe(model, source_root, score):
    return {
        "name": model.get("name") or "",
        "desc": model.get("desc") or "",
        "memory_path": model.get("memory_path") or "",
        "source_root": source_root,
        "score": score,
    }


def search_by_name(query):
    index = common.load_index()
    model = model_by_name(index, query)
    if model is None:
        return {"ok": True, "query": query, "matches": [], "skipped": []}
    roots = model.get("source_roots") or []
    root = roots[0] if roots else ""
    return {
        "ok": True,
        "query": query,
        "matched_by": "name",
        "matches": [describe(model, root, None)],
        "skipped": [],
    }


def search(query):
    normalized = common.norm_rel(query)
    index = common.load_index()
    hits = []
    skipped = []
    for model in index["models"]:
        if not isinstance(model, dict):
            continue
        name = str(model.get("name") or "")
        roots = model.get("source_roots") or []
        if not isinstance(roots, list) or not roots:
            skipped.append({"name": name, "reason": "缺少 source_roots"})
            continue
        best = None
        for root in roots:
            try:
                root_norm = common.norm_rel(str(root))
            except common.MemoryError as exc:
                skipped.append({"name": name, "reason": str(exc)})
                continue
            if common.is_under(normalized, root_norm):
                score = common.depth(root_norm)
                if best is None or score > best["score"]:
                    best = {"root": root_norm, "score": score}
        if best is None:
            continue
        hits.append(describe(model, best["root"], best["score"]))
    if not hits:
        named = model_by_name(index, query)
        result = {"ok": True, "query": normalized, "matches": [], "skipped": skipped}
        if named is not None:
            result["name_hit"] = named.get("name")
            result["hint"] = "路径未命中；同名模块已登记，使用 --name 查看"
        return result
    top = max(item["score"] for item in hits)
    return {
        "ok": True,
        "query": normalized,
        "matches": [item for item in hits if item["score"] == top],
        "skipped": skipped,
    }


def main():
    parser = argparse.ArgumentParser(description="按源码路径或模块名匹配记忆模块")
    parser.add_argument("--query", help="相对仓库根的文件或目录路径")
    parser.add_argument("--name", help="按模块名精确查询")
    args = parser.parse_args()
    if bool(args.query) == bool(args.name):
        common.fail("必须且只能提供 --query 或 --name 之一")
    try:
        if args.name:
            common.emit(search_by_name(args.name))
        else:
            common.emit(search(args.query))
    except common.MemoryError as exc:
        common.fail(str(exc))


if __name__ == "__main__":
    main()
