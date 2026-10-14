# -*- coding: utf-8 -*-
"""Shared paths, index IO, and fingerprint helpers for model memory."""

import hashlib
import json
import os
import sys

if sys.version_info < (3, 6):
    sys.stderr.write(
        '{"ok": false, "error": "\\u9700\\u8981 Python 3.6 \\u53ca\\u4ee5\\u4e0a\\u3002 '
        'python \u4e0d\u662f Python 3 \u65f6\u6539\u7528 python3 \u6216 py -3"}\n'
    )
    raise SystemExit(1)

from datetime import datetime, timezone
from pathlib import PurePosixPath

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
CONFIG_PATH = os.path.join(SKILL_DIR, "config", "fingerprint.yaml")


class MemoryError(Exception):
    pass


def _walk_up(start):
    current = os.path.abspath(start)
    while True:
        yield current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent


def _find_repo_root():
    """Locate the repository without requiring the index to exist.

    An existing index wins. Otherwise use the nearest .git from the working
    directory, then from the script directory. Nothing is created here.
    """
    starts = [os.getcwd(), SCRIPT_DIR]
    for start in starts:
        for current in _walk_up(start):
            if os.path.isfile(os.path.join(current, "ModelMemorys", "model-link.json")):
                return current
    for start in starts:
        for current in _walk_up(start):
            if os.path.exists(os.path.join(current, ".git")):
                return current
    return None


REPO_ROOT = None
MEMORY_ROOT = None
INDEX_PATH = None


def ensure_paths():
    global REPO_ROOT, MEMORY_ROOT, INDEX_PATH
    if REPO_ROOT:
        return
    REPO_ROOT = _find_repo_root()
    if not REPO_ROOT:
        raise MemoryError("未找到仓库根目录：向上没有 ModelMemorys/model-link.json 或 .git")
    MEMORY_ROOT = os.path.join(REPO_ROOT, "ModelMemorys")
    INDEX_PATH = os.path.join(MEMORY_ROOT, "model-link.json")

DEFAULT_INCLUDE = ["*"]
DEFAULT_EXCLUDE = ["verification.txt"]
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
        raise MemoryError("路径必须相对仓库根目录：%s" % path)
    parts = []
    for part in raw.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if not parts:
                raise MemoryError("路径越出仓库根目录：%s" % path)
            parts.pop()
            continue
        parts.append(part)
    if not parts:
        raise MemoryError("路径不能是仓库根目录")
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


def _parse_scalar(text):
    value = text.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def load_fingerprint_config():
    """Read the small config subset without a YAML dependency.

    Accepted shape:
        include:
          - "*.py"
        exclude:
          - "*.generated.*"
    An empty exclude list is honored. Omitted exclude falls back to the default.
    """
    if not os.path.isfile(CONFIG_PATH):
        return list(DEFAULT_INCLUDE), list(DEFAULT_EXCLUDE)
    include = []
    exclude = []
    seen_exclude = False
    section = None
    with open(CONFIG_PATH, "r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            stripped = line.split("#", 1)[0].rstrip()
            if not stripped.strip():
                continue
            if not line.startswith((" ", "\t")) and stripped.endswith(":"):
                section = stripped[:-1].strip()
                if section == "exclude":
                    seen_exclude = True
                continue
            if not line.startswith((" ", "\t")) and ":" in stripped:
                key, value = stripped.split(":", 1)
                if key.strip() in ("include", "exclude") and value.strip() not in ("", "[]"):
                    raise MemoryError(
                        "fingerprint.yaml:%d 只接受块状列表，不接受单行写法：%s"
                        % (line_no, stripped.strip())
                    )
            item = stripped.strip()
            if not item.startswith("- "):
                continue
            value = str(_parse_scalar(item[2:]))
            if section == "include":
                include.append(value)
            elif section == "exclude":
                exclude.append(value)
    if not include:
        include = list(DEFAULT_INCLUDE)
    if not seen_exclude:
        exclude = list(DEFAULT_EXCLUDE)
    return include, exclude


def _match_pattern(path, pattern):
    if pattern.startswith("/"):
        pattern = pattern[1:]
    path_obj = PurePosixPath(path)
    if "/" not in pattern and "**" not in pattern:
        return path_obj.match(pattern) or PurePosixPath(path_obj.name).match(pattern)
    return path_obj.match(pattern)


def selected(rel_path, include, exclude):
    if not any(_match_pattern(rel_path, pattern) for pattern in include):
        return False
    return not any(_match_pattern(rel_path, pattern) for pattern in exclude)


def iter_files(root, include, exclude):
    """Return {relative posix path: size} for selected files under root."""
    found = {}
    if not os.path.isdir(root):
        return found
    for current, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in (".git",)]
        for name in files:
            full = os.path.join(current, name)
            rel = os.path.relpath(full, root).replace("\\", "/")
            if name == "verification.txt" or not selected(rel, include, exclude):
                continue
            try:
                found[rel] = os.path.getsize(full)
            except OSError:
                continue
    return found


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


def fingerprint_entries(model):
    """Stable identity is '<source>|<relative path>' so different roots cannot collide.

    include/exclude apply only to source roots. Memory files are always included
    except verification.txt, so narrowing include cannot hide memory drift.
    """
    include, exclude = load_fingerprint_config()
    entries = {}
    warnings = []
    for root_rel in model.get("source_roots") or []:
        root_abs = source_root_abs(root_rel)
        if not os.path.isdir(root_abs):
            warnings.append("source_root 不是有效目录：%s" % root_rel)
            continue
        matched = iter_files(root_abs, include, exclude)
        if not matched:
            warnings.append("source_root 没有纳入文件：%s" % root_rel)
        for rel, size in matched.items():
            entries["src:%s|%s" % (root_rel, rel)] = size
    mem_rel_root = norm_memory_path(model)
    mem_abs = os.path.join(MEMORY_ROOT, mem_rel_root.replace("/", os.sep))
    for rel, size in iter_files(mem_abs, ["*"], []).items():
        entries["mem:%s" % rel] = size
    return entries, warnings


def norm_memory_path(model):
    raw = str(model.get("memory_path") or "").replace("\\", "/").strip()
    if raw.startswith("./"):
        raw = raw[2:]
    return norm_rel(raw)


def digest(entries):
    lines = ["%s\n%d\n" % (path, entries[path]) for path in sorted(entries)]
    payload = "".join(lines).encode("utf-8")
    return hashlib.md5(payload).hexdigest()


def read_verification(path):
    if not os.path.isfile(path):
        return None, None
    digest_line = None
    entries = {}
    with open(path, "r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            if digest_line is None:
                digest_line = line
                continue
            if "\t" not in line:
                continue
            rel, size_text = line.rsplit("\t", 1)
            try:
                entries[rel] = int(size_text)
            except ValueError:
                continue
    return digest_line, entries or None


def write_verification(directory, entries):
    os.makedirs(directory, exist_ok=True)
    value = digest(entries)
    stamped = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    path = os.path.join(directory, "verification.txt")
    temp = path + ".tmp"
    with open(temp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(value + "\n")
        handle.write(stamped + "\n")
        for rel in sorted(entries):
            handle.write("%s\t%d\n" % (rel, entries[rel]))
    os.replace(temp, path)
    return value


def diff_entries(previous, current):
    old = previous or {}
    added = [{"path": k, "size": current[k]} for k in sorted(current) if k not in old]
    removed = [{"path": k, "size": old[k]} for k in sorted(old) if k not in current]
    changed = [
        {"path": k, "old_size": old[k], "new_size": current[k]}
        for k in sorted(current)
        if k in old and old[k] != current[k]
    ]
    return {"added": added, "removed": removed, "changed": changed}


def is_under(query, root):
    if query.lower() == root.lower():
        return True
    prefix = root.lower().rstrip("/") + "/"
    return query.lower().startswith(prefix)


def depth(path):
    return len([p for p in path.split("/") if p])
