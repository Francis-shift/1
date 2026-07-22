"""快速核验:3 个错误案例确实失败、参考程序全过(房年朗自检用)。

在独立子进程里执行,避免死循环或异常污染主进程。
用法: python3 demo/run_case_check.py
"""
import os
import sys
import json
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cases.cases import CASES, REFERENCE  # noqa: E402

RUNNER = r"""
import sys, json, io, contextlib
src, tests_json = sys.argv[1], sys.argv[2]
tests = json.loads(tests_json)
ns, sink = {}, io.StringIO()
try:
    with contextlib.redirect_stdout(sink):
        exec(src, ns)
    fn = ns["search"]
except Exception as e:
    print(json.dumps({"passed": 0, "total": len(tests),
                      "mode": "load_error:" + type(e).__name__})); sys.exit(0)
passed, mode = 0, None
for args, expected in tests:
    try:
        with contextlib.redirect_stdout(sink):
            got = fn(*args)
        if got == expected:
            passed += 1
        else:
            mode = mode or "wrong_answer"
    except Exception as e:
        mode = mode or ("runtime_error:" + type(e).__name__)
print(json.dumps({"passed": passed, "total": len(tests),
                  "mode": mode or "all_passed"}))
"""

def run(src, tests):
    tests = [[list(a), e] for a, e in tests]
    p = subprocess.run([sys.executable, "-c", RUNNER, src, json.dumps(tests)],
                       capture_output=True, text=True,
                       stdin=subprocess.DEVNULL, timeout=10)
    return json.loads(p.stdout.strip().splitlines()[-1])

def main():
    ok = True
    for c in CASES:
        ref_r = run(REFERENCE, c["tests"])
        bug_r = run(c["buggy"], c["tests"])
        ref_ok = ref_r["mode"] == "all_passed"
        bug_fails = bug_r["mode"] != "all_passed"
        ok = ok and ref_ok and bug_fails
        print(f"[{c['id']}] {c['error_class']}")
        print(f"    参考程序: {ref_r}  {'✓' if ref_ok else '✗ 参考应全过!'}")
        print(f"    错误程序: {bug_r}  {'✓ 已复现失败' if bug_fails else '✗ 未复现失败!'}")
    print("\n总检:", "全部符合预期 ✓" if ok else "存在异常,请检查 ✗")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
