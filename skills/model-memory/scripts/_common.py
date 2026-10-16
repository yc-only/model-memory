# -*- coding: utf-8 -*-
"""Shared paths and index IO for model memory."""

import json
import os
import sys

if sys.version_info < (3, 6):
    sys.stderr.write(
        '{"ok": false, "error": "\\u9700\\u8981 Python 3.6 \\u53ca\\u4ee5\\u4e0a\\u3002 '
        'python \u4e0d\u662f Python 3 \u65f6\u6539\u7528 python3 \u6216 py -3"}\n'
    )
    raise SystemExit(1)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


class MemoryError(Exception):
    pass


def _find_repo_root():
    """Find the project by its memory index, starting at the working directory.

    The skill file location is not used, so a symlink or global install still
    follows the project being worked in. If the working directory is nested
    inside the project, walk upward to the existing ModelMemorys index.
    """
    current = os.getcwd()
    while True:
        if os.path.isfile(os.path.join(current, "ModelMemorys", "model-link.json")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return os.getcwd()
        current = parent


REPO_ROOT = None
MEMORY_ROOT = None
INDEX_PATH = None


def ensure_paths():
    global REPO_ROOT, MEMORY_ROOT, INDEX_PATH
    if REPO_ROOT:
        return
    REPO_ROOT = _find_repo_root()
    if not REPO_ROOT:
        raise MemoryError("未找到当前工作目录")
    MEMORY_ROOT = os.path.join(REPO_ROOT, "ModelMemorys")
    INDEX_PATH = os.path.join(MEMORY_ROOT, "model-link.json")

NAME_OK = set("abcdefghijklmnopqrstuvwxyz0123456789-")


def fail(message):
    sys.stderr.write(json.dumps({"ok": False, "error": message}, ensure_ascii=False) + "\n")
    raise SystemExit(1)


def emit(payload):
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def norm_rel(path):
    """Normalize a repo-relative path to forward slashes without a trailing slash."""
    raw = (path or "").strip().replace("\\", "/")
    if not raw:
        raise MemoryError("路径为空")
    if raw.startswith("/") or (len(raw) >= 2 and raw[1] == ":"):
        raise MemoryError("路径必须相对项目根目录：%s" % path)
    parts = []
    for part in raw.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if not parts:
                raise MemoryError("路径越出项目根目录：%s" % path)
            parts.pop()
            continue
        parts.append(part)
    if not parts:
        raise MemoryError("路径不能是项目根目录")
    return "/".join(parts)


def load_index(create=False):
    ensure_paths()
    if not os.path.isfile(INDEX_PATH):
        if not create:
            raise MemoryError("缺少索引：ModelMemorys/model-link.json。首次创建模块时会自动生成")
        save_index({"models": []})
    try:
        with open(INDEX_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError) as exc:
        raise MemoryError("索引无法读取：%s" % exc)
    if not isinstance(data, dict) or not isinstance(data.get("models"), list):
        raise MemoryError("索引格式错误：需要 {\"models\": []}")
    return data


def save_index(data):
    ensure_paths()
    os.makedirs(MEMORY_ROOT, exist_ok=True)
    temp = INDEX_PATH + ".tmp"
    with open(temp, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(temp, INDEX_PATH)


def find_model(data, name):
    for item in data["models"]:
        if isinstance(item, dict) and item.get("name") == name:
            return item
    return None


def validate_name(name):
    if not name or any(ch not in NAME_OK for ch in name) or name.startswith("-") or name.endswith("-"):
        raise MemoryError("模块名只能是小写字母、数字、连字符，且不能以连字符开头或结尾")
    return name


def memory_dir(name):
    ensure_paths()
    return os.path.join(MEMORY_ROOT, name)


def source_root_abs(root_rel):
    ensure_paths()
    return os.path.join(REPO_ROOT, root_rel.replace("/", os.sep))


def require_source_dir(root_rel):
    """Reject a source root that is missing or not a directory."""
    root_abs = source_root_abs(root_rel)
    if not os.path.exists(root_abs):
        raise MemoryError("source_root 不存在：%s" % root_rel)
    if not os.path.isdir(root_abs):
        raise MemoryError("source_root 必须是目录：%s" % root_rel)
    return root_abs


def is_under(query, root):
    if query.lower() == root.lower():
        return True
    prefix = root.lower().rstrip("/") + "/"
    return query.lower().startswith(prefix)


def depth(path):
    return len([p for p in path.split("/") if p])
