#!/usr/bin/env python3
"""A minimal Codex CLI app backed by OpenAI Responses API."""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from typing import Any
from urllib import error, request

API_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-5.3-codex"


class CodexAppError(RuntimeError):
    """Application-level exception with user-friendly messages."""


def build_payload(prompt: str, model: str) -> dict[str, Any]:
    cleaned = prompt.strip()
    if not cleaned:
        raise CodexAppError("prompt 不能为空")

    return {
        "model": model,
        "input": cleaned,
    }


def extract_text(response_json: dict[str, Any]) -> str:
    output = response_json.get("output", [])
    parts: list[str] = []

    for item in output:
        content = item.get("content", [])
        for block in content:
            if block.get("type") == "output_text" and block.get("text"):
                parts.append(block["text"])

    if parts:
        return "\n".join(parts).strip()

    fallback = response_json.get("output_text")
    if isinstance(fallback, str) and fallback.strip():
        return fallback.strip()

    raise CodexAppError("接口返回里没有可读文本")


def query_codex(prompt: str, model: str = DEFAULT_MODEL) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise CodexAppError("缺少 OPENAI_API_KEY 环境变量")

    payload = build_payload(prompt, model)
    data = json.dumps(payload).encode("utf-8")

    req = request.Request(
        API_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise CodexAppError(f"接口请求失败（HTTP {exc.code}）: {detail}") from exc
    except error.URLError as exc:
        raise CodexAppError(f"网络错误: {exc.reason}") from exc

    try:
        response_json = json.loads(body)
    except json.JSONDecodeError as exc:
        raise CodexAppError("接口返回不是合法 JSON") from exc

    return extract_text(response_json)


def run_self_check() -> int:
    print("Codex 本机自检：")
    print(f"- Python 版本: {platform.python_version()}")
    print(f"- 平台: {platform.system()} {platform.release()}")

    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        masked = f"{api_key[:7]}...{api_key[-4:]}" if len(api_key) > 12 else "***已设置***"
        print(f"- OPENAI_API_KEY: 已设置 ({masked})")
    else:
        print("- OPENAI_API_KEY: 未设置")
        print("  修复建议: export OPENAI_API_KEY='你的密钥'")

    req = request.Request(
        API_URL,
        data=json.dumps({"model": DEFAULT_MODEL, "input": "ping"}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key or 'missing'}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=15) as resp:
            status = resp.getcode()
            print(f"- 网络/API: 可访问 (HTTP {status})")
    except error.HTTPError as exc:
        if exc.code == 401:
            print("- 网络/API: 可访问，但鉴权失败 (401)")
            print("  修复建议: 检查 OPENAI_API_KEY 是否正确、是否过期。")
        else:
            print(f"- 网络/API: HTTP {exc.code}")
            print("  修复建议: 检查代理/防火墙，或稍后再试。")
    except error.URLError as exc:
        print(f"- 网络/API: 连接失败 ({exc.reason})")
        print("  修复建议: 检查网络、DNS、公司代理或防火墙策略。")

    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Codex 命令行应用")
    parser.add_argument("prompt", nargs="?", help="你要发送给 Codex 的提示词")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="模型名称")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="进入交互模式（输入 /exit 退出）",
    )
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="检查本机 Codex 常见问题（环境变量/网络/鉴权）",
    )
    return parser.parse_args(argv)


def run_interactive(model: str) -> int:
    print("已进入 Codex 交互模式，输入 /exit 退出。")
    while True:
        try:
            prompt = input("你> ").strip()
        except EOFError:
            print()
            break

        if not prompt:
            continue
        if prompt in {"/exit", "exit", "quit"}:
            break

        try:
            answer = query_codex(prompt, model)
        except CodexAppError as exc:
            print(f"错误: {exc}", file=sys.stderr)
            continue

        print(f"Codex> {answer}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ns = parse_args(sys.argv[1:] if argv is None else argv)

    if ns.self_check:
        return run_self_check()

    if ns.interactive:
        return run_interactive(ns.model)

    if not ns.prompt:
        print("错误: 请提供 prompt，或使用 --interactive 进入交互模式。", file=sys.stderr)
        return 2

    try:
        answer = query_codex(ns.prompt, ns.model)
    except CodexAppError as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1

    print(answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
