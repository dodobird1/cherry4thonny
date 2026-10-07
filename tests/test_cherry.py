import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from cherry.hints import UNKNOWN, explain_error, latest_error, looks_like_error
from cherry.reply import deletion_span, message_for, parse_reply
from sakura_plugin.plugin import CherryBridge, _handler, bridge_file


def test_offline_notes_cover_the_common_errors():
    assert "冒号" in explain_error("SyntaxError: expected ':'")
    assert "名字" in explain_error("NameError: name 'cat' is not defined")
    assert "空格" in explain_error("IndentationError: unexpected indent")
    assert explain_error("ZeroDivisionError: division by zero") == UNKNOWN


def test_unknown_note_is_not_presented_as_a_model_reply():
    assert "小鸟" not in UNKNOWN
    assert "模型" not in UNKNOWN


def test_latest_error_keeps_the_last_traceback():
    shell = "print(1)\nTraceback (most recent call last):\nNameError: name 'a' is not defined\n"
    assert latest_error(shell).startswith("Traceback")
    assert looks_like_error(shell)


def test_guide_modes_drop_marks_even_if_the_model_adds_them():
    reply = "先看这一行。\n标记删除：print(\n标记打出：print(1)"
    parsed = parse_reply("what", reply)
    assert parsed["delete_text"] == ""
    assert parsed["type_text"] == ""
    assert "先看这一行" in parsed["hint"]


def test_stuck_keeps_one_short_line_and_does_not_rewrite_the_source():
    source = "print(\n"
    parsed = parse_reply("stuck", "少了右边。\n标记删除：print(\n标记打出：print(\"你好\")")
    assert parsed["delete_text"] == "print("
    assert parsed["type_text"] == 'print("你好")'
    before = source
    span = deletion_span(source, parsed["delete_text"])
    assert span == (0, 6)
    assert source == before


def test_long_type_line_is_dropped():
    parsed = parse_reply("stuck", "标记打出：" + ("啊" * 81))
    assert parsed["type_text"] == ""


def test_message_uses_the_button_and_not_a_free_description():
    text = message_for("error", selection="print(", error="SyntaxError: invalid syntax", nearby="")
    assert text.startswith("看报错")
    assert "print(" in text
    assert "描述" not in text


def test_bridge_handler_rejects_a_bad_token_and_returns_the_reply(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    seen = {}

    def reply(text: str) -> str:
        seen["text"] = text
        return "先看冒号。"

    server = ThreadingHTTPServer(("127.0.0.1", 0), _handler("secret", reply))
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        denied = Request(f"http://127.0.0.1:{port}/turn", data=b"{}", method="POST")
        try:
            urlopen(denied)
            raise AssertionError("missing token should be refused")
        except HTTPError as error:
            assert error.code == 403
        accepted = Request(
            f"http://127.0.0.1:{port}/turn",
            data=json.dumps({"text": "看报错"}).encode(),
            headers={"Authorization": "Bearer secret"},
            method="POST",
        )
        with urlopen(accepted) as response:
            body = json.loads(response.read())
        assert body["reply"] == "先看冒号。"
        assert seen["text"] == "看报错"
    finally:
        server.shutdown()
        server.server_close()
    assert bridge_file() == Path(tmp_path) / "cherry" / "bridge.json"
    assert CherryBridge is not None
