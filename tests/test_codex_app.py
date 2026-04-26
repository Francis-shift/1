import unittest
from unittest import mock

from codex_app import CodexAppError, build_payload, extract_text, main, parse_args


class CodexAppTests(unittest.TestCase):
    def test_build_payload_strips_prompt(self):
        payload = build_payload("  hello  ", "gpt-5.3-codex")
        self.assertEqual(payload["input"], "hello")
        self.assertEqual(payload["model"], "gpt-5.3-codex")

    def test_build_payload_rejects_empty_prompt(self):
        with self.assertRaises(CodexAppError):
            build_payload("   ", "gpt-5.3-codex")

    def test_extract_text_from_output_content(self):
        response_json = {
            "output": [
                {
                    "content": [
                        {"type": "output_text", "text": "第一行"},
                        {"type": "output_text", "text": "第二行"},
                    ]
                }
            ]
        }
        self.assertEqual(extract_text(response_json), "第一行\n第二行")

    def test_extract_text_fallback_output_text(self):
        response_json = {"output": [], "output_text": "fallback"}
        self.assertEqual(extract_text(response_json), "fallback")

    def test_extract_text_raises_when_missing(self):
        with self.assertRaises(CodexAppError):
            extract_text({"output": []})

    def test_parse_args_interactive_without_prompt(self):
        ns = parse_args(["--interactive"])
        self.assertTrue(ns.interactive)
        self.assertIsNone(ns.prompt)

    def test_parse_args_self_check(self):
        ns = parse_args(["--self-check"])
        self.assertTrue(ns.self_check)

    @mock.patch("codex_app.query_codex")
    def test_main_requires_prompt_or_interactive(self, _mock_query_codex):
        rc = main([])
        self.assertEqual(rc, 2)

    @mock.patch("codex_app.run_self_check", return_value=0)
    def test_main_runs_self_check(self, mock_self_check):
        rc = main(["--self-check"])
        self.assertEqual(rc, 0)
        mock_self_check.assert_called_once()


if __name__ == "__main__":
    unittest.main()
