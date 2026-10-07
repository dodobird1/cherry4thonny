"""Fixed simple-Chinese notes used when the model cannot be reached."""

from __future__ import annotations


OFFLINE_LABEL = "离线提示"
UNKNOWN = "这是程序给出的英文报错。先看它指出的那一行。"
UNREACHABLE = "现在连不上小鸟。先按「看报错」。"


def explain_error(traceback_text: str) -> str:
    """Return a prepared note. This is not a model reply."""

    text = traceback_text or ""
    lowered = text.casefold()
    if "indentationerror" in lowered or "unexpected indent" in lowered or "expected an indented block" in lowered:
        return "空格没有对齐。这一行要和上面的行对齐。"
    if "nameerror" in lowered or "is not defined" in lowered:
        return "这个名字还没有写过。先看看是不是打错了。"
    if "expected ':'" in lowered or "invalid syntax" in lowered:
        return "这一行少了冒号。"
    return UNKNOWN


def looks_like_error(shell_text: str) -> bool:
    lowered = (shell_text or "").casefold()
    return any(token in lowered for token in ("traceback", "error", "exception"))


def latest_error(shell_text: str) -> str:
    """Keep the last traceback-sized chunk from the shell."""

    lines = (shell_text or "").splitlines()
    start = 0
    for index, line in enumerate(lines):
        if line.startswith("Traceback"):
            start = index
    if start == 0 and lines and not lines[0].startswith("Traceback"):
        for index, line in enumerate(lines):
            if "Error" in line or "Exception" in line:
                start = index
    chunk = "\n".join(lines[start:]).strip()
    return chunk[-4000:]
