# Codex 应用（命令行版）

这是一个可直接运行的最小 Codex 命令行应用。

## 功能

- 读取命令行里的提示词（prompt）
- 通过 OpenAI Responses API 获取回答
- 支持自定义模型（默认 `gpt-5.3-codex`）
- 对常见错误（缺少 API Key、网络失败、接口报错）给出清晰提示

## 快速开始

1. 设置环境变量：

```bash
export OPENAI_API_KEY="你的密钥"
```

2. 运行：

```bash
python3 codex_app.py "帮我写一个 Python 快速排序"
```

3. 可选参数：

```bash
python3 codex_app.py "解释这个正则" --model gpt-5.3-codex
```

4. 打开交互模式（更像“打开 Codex”）：

```bash
python3 codex_app.py --interactive
```

输入 `/exit` 可退出。

5. 如果你要修复“我电脑上的 Codex 应用”，先跑自检：

```bash
python3 codex_app.py --self-check
```

这个模式会检查：
- Python 版本和系统信息
- `OPENAI_API_KEY` 是否存在
- 是否能连通 OpenAI API（并区分网络错误与鉴权错误）

## 说明

- 本应用使用标准库 `urllib` 发送 HTTP 请求，不依赖第三方包。
- 如果你需要集成到 Web 服务，可在 `query_codex` 基础上封装路由层。
