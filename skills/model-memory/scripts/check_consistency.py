# -*- coding: utf-8 -*-
"""Compare a module fingerprint with verification.txt.

Usage:
    python check_consistency.py --module <name>
    python check_consistency.py --module <name> --write
"""

import argparse
import os

import _common as common


def check(name, write):
    module_name = common.validate_name(name)
    index = common.load_index()
    model = common.find_model(index, module_name)
    if model is None:
        raise common.MemoryError("索引中不存在模块：%s" % module_name)
    directory = os.path.join(common.MEMORY_ROOT, common.norm_memory_path(model).replace("/", os.sep))
    if not os.path.isdir(directory):
        raise common.MemoryError("记忆目录不存在：%s" % model.get("memory_path"))

    current, warnings = common.fingerprint_entries(model)
    current_digest = common.digest(current)
    verification = os.path.join(directory, "verification.txt")
    recorded, previous = common.read_verification(verification)
    stored_match = recorded == current_digest and previous is not None
    consistent = stored_match and not warnings

    if write:
        if warnings:
            raise common.MemoryError("；".join(warnings))
        rewritten = not stored_match
        written = common.write_verification(directory, current) if rewritten else recorded
        result = {
            "ok": True,
            "module": module_name,
            "rewritten": rewritten,
            "written": written,
            "file_count": len(current),
        }
        if rewritten:
            if recorded is not None:
                result["previous"] = recorded
        else:
            result["reason"] = "already_consistent"
        return result

    result = {
        "ok": True,
        "module": module_name,
        "consistent": consistent,
        "verdict": "TRUE" if consistent else "FALSE",
        "file_count": len(current),
    }
    if warnings:
        result["warnings"] = warnings
    if not stored_match:
        result.update(common.diff_entries(previous, current))
        result["reason"] = "missing_verification" if recorded is None else "fingerprint_mismatch"
    elif warnings:
        result["reason"] = "source_not_tracked"
    return result


def main():
    parser = argparse.ArgumentParser(description="检查模块记忆指纹是否与当前文件一致")
    parser.add_argument("--module", required=True, help="模块名")
    parser.add_argument("--write", action="store_true", help="用当前文件重写 verification.txt")
    args = parser.parse_args()
    try:
        common.emit(check(args.module, args.write))
    except common.MemoryError as exc:
        common.fail(str(exc))


if __name__ == "__main__":
    main()
