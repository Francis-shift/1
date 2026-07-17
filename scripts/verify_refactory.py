"""数据层验证脚本 1:Refactory benchmark(question_1)

验证内容:
1. 数据规模与 README/论文描述是否一致(reference/correct/wrong 数量)
2. 错误程序能否直接对测试用例执行 —— 证明"错误程序 + 测试用例"可用
3. 产出 D 维(调试与执行)画像特征示例:
   每个错误程序的 通过率 / 失败模式(答案错误 vs 运行异常),
   以及整体错误类型分布 —— 这就是画像特征提取的最小雏形。

用法: python3 scripts/verify_refactory.py <refactory_repo_path>/data/question_1
"""
import sys
import glob
import os
import io
import json
import contextlib
from collections import Counter

def load_tests(qdir):
    tests = []
    for inp in sorted(glob.glob(os.path.join(qdir, "ans", "input_*.txt"))):
        out = inp.replace("input_", "output_")
        with open(inp) as f1, open(out) as f2:
            tests.append((f1.read().strip(), f2.read().strip()))
    return tests

def run_program(path, tests):
    """在隔离命名空间中执行学生程序,逐个测试用例调用。"""
    with open(path) as f:
        src = f.read()
    ns = {}
    sink = io.StringIO()  # 屏蔽学生程序里的 print 输出
    try:
        with contextlib.redirect_stdout(sink):
            exec(src, ns)  # noqa: S102 - 受控数据集,研究用途
    except Exception as e:
        return {"passed": 0, "total": len(tests), "mode": f"load_error:{type(e).__name__}"}
    passed, fail_mode = 0, None
    for expr, expected in tests:
        try:
            with contextlib.redirect_stdout(sink):
                result = eval(expr, ns)  # noqa: S307
            if str(result) == expected:
                passed += 1
            else:
                fail_mode = fail_mode or "wrong_answer"
        except Exception as e:
            fail_mode = fail_mode or f"runtime_error:{type(e).__name__}"
    return {"passed": passed, "total": len(tests), "mode": fail_mode or "all_passed"}

def main(qdir, sample_n=100):
    tests = load_tests(qdir)
    counts = {k: len(glob.glob(os.path.join(qdir, "code", k, "*.py")))
              for k in ("reference", "correct", "wrong")}
    print(f"[规模核对] {counts},测试用例 {len(tests)} 个")

    ref = glob.glob(os.path.join(qdir, "code", "reference", "*.py"))[0]
    print(f"[参考程序] {os.path.basename(ref)} -> {run_program(ref, tests)}")

    wrongs = sorted(glob.glob(os.path.join(qdir, "code", "wrong", "*.py")))[:sample_n]
    results, modes = [], Counter()
    for w in wrongs:
        r = run_program(w, tests)
        r["file"] = os.path.basename(w)
        results.append(r)
        modes[r["mode"]] += 1

    pass_rates = [r["passed"] / r["total"] for r in results]
    print(f"\n[D 维特征示例] 对前 {len(results)} 个错误程序:")
    print(f"  平均测试通过率: {sum(pass_rates)/len(pass_rates):.2%}")
    print(f"  失败模式分布: {dict(modes)}")
    print("  单个程序示例(前 5 个):")
    for r in results[:5]:
        print(f"    {r['file']}: 通过 {r['passed']}/{r['total']},模式={r['mode']}")

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "output_refactory_features.json")
    with open(out, "w") as f:
        json.dump(results, f, indent=1, ensure_ascii=False)
    print(f"\n[输出] 逐程序特征已写入 {out}")

if __name__ == "__main__":
    main(sys.argv[1])
