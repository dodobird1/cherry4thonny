# cherry

樱桃是 Thonny 的插件。学生按中文按钮，把选中的代码或最近一次报错交给 Sakura。小鸟先用短中文提示。只有按下「还是不会」以后，编辑器里已有的字才会被标红，要新打的一行用绿色显示在旁边。插件不会把字写进编辑器，也不会替学生运行程序。

同一套插件可以装在 sakura-trunk 上，也可以装在完整的 Sakura 上。它只用两边都有的对话接口，不需要语音、语音识别、屏幕感知、联网或 MCP。

## 许可证

CC BY-NC-ND 4.0。Copyright (c) 2026 dodobird1 and the HT^2 club。

谢谢 Thonny 的开发者，也谢谢 Sakura 的开发者。dodobird1 是 Sakura 的贡献者之一，这里谢谢 Thonny 的作者，也谢谢一起做 Sakura 的其他人。

Thonny 仍使用它自己的 MIT 许可证，Copyright (c) 2024 Aivar Annamaa。这个仓库不重新发布 Thonny。

## 安装

在装有 Thonny 的环境里：

```bash
pip install -e .
```

Thonny 会从 `thonnycontrib` 加载 `load_plugin`。重启 Thonny 后，编辑菜单和「樱桃」视图里有这些按钮：看报错、这是什么、哪里不对、下一步、还是不会。

把 `sakura_plugin` 目录复制到 Sakura 用户数据里的 `plugins/user/cherry.bridge`，然后在插件页启用「樱桃」。sakura-trunk 和完整 Sakura 都是这个路径。桥只监听本机，并把地址写在：

- Linux：`~/.local/share/cherry/bridge.json`
- Windows：`%APPDATA%\cherry\bridge.json`

连不上桥时，「看报错」仍会给出少冒号、名字没写过、空格没对齐这几种固定说明。那是离线提示，不是小鸟的回答。
