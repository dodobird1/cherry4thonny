"""Thonny buttons for cherry. The editor text is never inserted or deleted here."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from cherry.bridge_client import BridgeUnavailable, ask
from cherry.hints import OFFLINE_LABEL, UNREACHABLE, explain_error, latest_error, looks_like_error
from cherry.reply import deletion_span, message_for, parse_reply

DELETE_TAG = "cherry_delete"
MODES = (
    ("error", "看报错"),
    ("what", "这是什么"),
    ("wrong", "哪里不对"),
    ("next", "下一步"),
    ("stuck", "还是不会"),
)


class CherryView(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.hint = tk.Text(self, height=8, wrap="word", font=("TkDefaultFont", 16))
        self.hint.pack(fill="both", expand=True, padx=8, pady=8)
        self.hint.insert("1.0", "选中代码，或者运行出错以后，按下面的按钮。")
        self.hint.configure(state="disabled")
        self.type_label = tk.Label(self, text="", justify="left", anchor="w", font=("TkFixedFont", 16))
        self.type_label.pack(fill="x", padx=8, pady=(0, 8))
        buttons = ttk.Frame(self)
        buttons.pack(fill="x", padx=8, pady=(0, 8))
        for mode, label in MODES:
            ttk.Button(buttons, text=label, command=lambda mode=mode: run_mode(mode, self)).pack(
                side="left", padx=4
            )
        self._last_hint = ""

    def show(self, title: str, hint: str, type_text: str) -> None:
        self._last_hint = hint
        self.hint.configure(state="normal")
        self.hint.delete("1.0", "end")
        self.hint.insert("1.0", f"{title}\n\n{hint}")
        self.hint.configure(state="disabled")
        if type_text:
            self.type_label.configure(text=f"请你自己打出：{type_text}", bg="#c8f0c4")
        else:
            self.type_label.configure(text="", bg="#f7f4ef")


def load_plugin() -> None:
    from thonny import get_workbench

    workbench = get_workbench()
    workbench.add_view(CherryView, "樱桃", "ne", visible_by_default=True)
    for mode, label in MODES:
        workbench.add_command(
            f"cherry_{mode}",
            "edit",
            label,
            lambda _event=None, mode=mode: run_mode(mode),
            tester=lambda _event=None, mode=mode: _tester(mode),
            group=180,
        )


def run_mode(mode: str, view: CherryView | None = None) -> None:
    from thonny import get_workbench

    view = view or get_workbench().get_view("CherryView")
    selection = _selection()
    error = latest_error(_shell_text()) if mode in {"error", "wrong", "stuck"} else ""
    nearby = "" if selection else _nearby()
    if mode == "error" and not looks_like_error(error):
        _show(view, OFFLINE_LABEL, "现在还没有报错。先运行一次程序。", "")
        return
    text = message_for(mode, selection=selection, error=error, nearby=nearby)
    try:
        reply = ask(text)
    except BridgeUnavailable:
        if mode == "error":
            _show(view, OFFLINE_LABEL, explain_error(error), "")
        else:
            _show(view, OFFLINE_LABEL, UNREACHABLE, "")
        _clear_marks()
        return
    parsed = parse_reply(mode, reply)
    missing = _mark_delete(parsed["delete_text"], selection)
    hint = parsed["hint"] or "小鸟没有说出新的话。"
    if missing:
        hint = f"{hint}\n\n没有在代码里找到要标红的字。"
    _show(view, "小鸟说", hint, parsed["type_text"])


def _tester(mode: str) -> bool:
    if mode == "error":
        return looks_like_error(_shell_text())
    if mode == "stuck":
        return bool(_selection())
    return bool(_selection())


def _selection() -> str:
    widget = _editor_widget()
    if widget is None:
        return ""
    try:
        return widget.get("sel.first", "sel.last")
    except tk.TclError:
        return ""


def _nearby() -> str:
    widget = _editor_widget()
    if widget is None:
        return ""
    try:
        line = int(str(widget.index("insert")).split(".")[0])
    except (tk.TclError, ValueError):
        return ""
    start = max(1, line - 2)
    end = line + 2
    try:
        return widget.get(f"{start}.0", f"{end}.0").strip()
    except tk.TclError:
        return ""


def _shell_text() -> str:
    from thonny import get_workbench

    shell = get_workbench().get_view("ShellView", create=False)
    if shell is None or not hasattr(shell, "text"):
        return ""
    try:
        return shell.text.get("1.0", "end")
    except tk.TclError:
        return ""


def _editor_widget():
    from thonny import get_workbench

    notebook = get_workbench().get_editor_notebook()
    editor = notebook.get_current_editor() if notebook is not None else None
    if editor is None:
        return None
    return editor.get_text_widget()


def _mark_delete(needle: str, selection: str) -> bool:
    """Paint red on existing characters. Return True when the needle was not found."""

    widget = _editor_widget()
    if widget is None:
        return bool(needle)
    try:
        widget.tag_remove(DELETE_TAG, "1.0", "end")
        widget.tag_configure(DELETE_TAG, background="#f4b4b4")
    except tk.TclError:
        return bool(needle)
    if not needle:
        return False
    source = selection or widget.get("1.0", "end-1c")
    span = deletion_span(source, needle)
    if span is None:
        return True
    start, end = _indexes_for_span(widget, selection, span)
    if start is None:
        return True
    widget.tag_add(DELETE_TAG, start, end)
    return False


def _indexes_for_span(widget, selection: str, span: tuple[int, int]):
    start_off, end_off = span
    if selection:
        try:
            origin = widget.index("sel.first")
        except tk.TclError:
            origin = "1.0"
    else:
        origin = "1.0"
    try:
        start = widget.index(f"{origin}+{start_off}c")
        end = widget.index(f"{origin}+{end_off}c")
    except tk.TclError:
        return None, None
    return start, end


def _clear_marks() -> None:
    widget = _editor_widget()
    if widget is None:
        return
    try:
        widget.tag_remove(DELETE_TAG, "1.0", "end")
    except tk.TclError:
        return


def _show(view: CherryView | None, title: str, hint: str, type_text: str) -> None:
    if view is not None:
        view.show(title, hint, type_text)
