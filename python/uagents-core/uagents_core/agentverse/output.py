import json
import os
import re
import sys
from collections import Counter
from typing import Any

_JSON_KEY_LINE = re.compile(r'^(\s*)("[^"\\]*(?:\\.[^"\\]*)*")\s*(:)(.*)$')


def use_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _wrap_sgr(sgr_code: str, text: str) -> str:
    if not use_color():
        return text
    return f"\033[{sgr_code}m{text}\033[0m"


def dim(text: str) -> str:
    return _wrap_sgr("2", text)


def green(text: str) -> str:
    return _wrap_sgr("32", text)


def yellow(text: str) -> str:
    return _wrap_sgr("33", text)


def red(text: str) -> str:
    return _wrap_sgr("31", text)


def cyan(text: str) -> str:
    return _wrap_sgr("36", text)


_need_section_gap = False


def reset_sections() -> None:
    global _need_section_gap
    _need_section_gap = False


def section(title: str) -> None:
    global _need_section_gap
    if _need_section_gap:
        print()
    _need_section_gap = True
    if use_color():
        print(f"\033[1;2m{title}\033[0m")
    else:
        print(title)


def _indent(prefix: str, message: str) -> None:
    print(f"  {prefix} {message}")


def ok(message: str) -> None:
    _indent(green("✓"), message)


def warn(message: str) -> None:
    _indent(yellow("!"), message)


def err(message: str) -> None:
    _indent(red("✖"), message)


def info(message: str) -> None:
    _indent(dim("·"), message)


def print_json(data: Any, *, indent: int = 2) -> None:
    text = json.dumps(data, indent=indent, ensure_ascii=False, sort_keys=True)
    gutter = dim("  │ ")
    for line in text.splitlines():
        m = _JSON_KEY_LINE.match(line)
        if m:
            print(
                gutter
                + m.group(1)
                + cyan(m.group(2))
                + m.group(3)
                + m.group(4)
            )
        else:
            print(gutter + line)


def print_readme(text: str) -> None:
    text = text.replace("\r\n", "\n")
    gutter = dim("  │ ")
    for line in text.splitlines():
        if line.strip() == "":
            print()
        else:
            print(gutter + line)


def _fmt_diff_val(value: Any) -> str:
    if isinstance(value, (dict, list)):
        try:
            return json.dumps(value, sort_keys=True, default=str)
        except (TypeError, ValueError):
            return repr(value)
    return repr(value)


def dict_diff(
    left: dict[str, Any],
    right: dict[str, Any],
    *,
    left_name: str = "almanac",
    right_name: str = "marketplace",
) -> None:
    """Shallow diff: print detail lines with info()."""
    for key in sorted(left.keys() - right.keys()):
        info(f"{key} — only {left_name}: {_fmt_diff_val(left[key])}")
    for key in sorted(right.keys() - left.keys()):
        info(f"{key} — only {right_name}: {_fmt_diff_val(right[key])}")
    for key in sorted(left.keys() & right.keys()):
        if left[key] != right[key]:
            info(
                f"{key} — {left_name}: {_fmt_diff_val(left[key])} | "
                f"{right_name}: {_fmt_diff_val(right[key])}"
            )


def list_diff(
    left: list[Any],
    right: list[Any],
    *,
    left_name: str = "almanac",
    right_name: str = "marketplace",
) -> None:
    """Multiset diff (order ignored): print detail lines with info()."""
    ca, cb = Counter(left), Counter(right)
    for x, n in sorted((ca - cb).items()):
        suffix = f" ({n}×)" if n > 1 else ""
        info(f"Only {left_name}{suffix}: {x}")
    for x, n in sorted((cb - ca).items()):
        suffix = f" ({n}×)" if n > 1 else ""
        info(f"Only {right_name}{suffix}: {x}")
