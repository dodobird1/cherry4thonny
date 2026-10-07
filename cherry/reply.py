"""Turn a model reply into a hint and optional marks. Marks never change the file."""

from __future__ import annotations

DELETE_PREFIX = "标记删除："
TYPE_PREFIX = "标记打出："
MAX_MARK_CHARS = 80


def message_for(mode: str, *, selection: str, error: str, nearby: str) -> str:
    code = (selection or nearby or "").strip()
    if mode == "error":
        head = "看报错。"
        tail = "请用很短的中文说明。先不要标出要删的字，也不要给出要打的新字。"
    elif mode == "what":
        head = "这是什么。"
        tail = "请用很短的中文说明这段在做什么。先不要标出要删的字。"
    elif mode == "wrong":
        head = "哪里不对。"
        tail = "请用很短的中文指出该看哪一行。先不要标出要删的字。"
    elif mode == "next":
        head = "下一步。"
        tail = "请只说接下来的一小步。不要给整段程序，也不要标出要删的字。"
    elif mode == "stuck":
        head = "还是不会。"
        tail = (
            "请先用一两句中文说原因。然后另起两行，每行都要短：\n"
            "标记删除：编辑器里原样存在的几个字\n"
            "标记打出：一行新字"
        )
    else:
        raise ValueError(mode)
    parts = [head, ""]
    if code:
        parts.extend(["这一段：", code, ""])
    if error.strip():
        parts.extend(["程序说：", error.strip(), ""])
    parts.append(tail)
    return "\n".join(parts)


def parse_reply(mode: str, reply: str) -> dict[str, str]:
    hint_lines: list[str] = []
    delete_text = ""
    type_text = ""
    for line in (reply or "").splitlines():
        if line.startswith(DELETE_PREFIX):
            delete_text = line[len(DELETE_PREFIX):].strip()
        elif line.startswith(TYPE_PREFIX):
            type_text = line[len(TYPE_PREFIX):].strip()
        else:
            hint_lines.append(line)
    hint = "\n".join(hint_lines).strip()
    if mode != "stuck":
        delete_text = ""
        type_text = ""
    if "\n" in type_text or len(type_text) > MAX_MARK_CHARS:
        type_text = ""
    if "\n" in delete_text or len(delete_text) > MAX_MARK_CHARS:
        delete_text = ""
    return {"hint": hint, "delete_text": delete_text, "type_text": type_text}


def deletion_span(source: str, needle: str) -> tuple[int, int] | None:
    """Locate text to mark red. The source string is not rewritten."""

    if not needle or needle not in source:
        return None
    start = source.find(needle)
    return start, start + len(needle)
