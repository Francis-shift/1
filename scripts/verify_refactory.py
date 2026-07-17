"""数据层验证脚本 1:Refactory benchmark(question_1)

验证内容:
1. 数据规模与 README/论文描述是否一致(reference/correct/wrong 数量)
2. 错误程序能否直接对测试用例执行 —— 证明"错误程序 + 测试用例"可用
3. 产出 D 维(调试与执行)**提交级候选特征**示例:
   每个错误程序的 通过率 / 失败模式(答案错误 vs 运行异常),
   以及整体错误类型分布。

口径说明:
 - Refactory 的 wrong_x_yyy.py 文件名不含学生 ID,无法把同一学生的
   多次提交串起来,因此这里算出的是"程序/提交级"特征,还不是
   "学习者级"画像;学习者级聚合需要 CS1QA(有匿名学生 ID)或
   CodeWorkout(有 SubjectID)这类数据。

安全说明:
 - 每个学生程序在**独立子进程**中执行(stdin 关闭、stdout 丢弃),
   单程序超时 10 秒,死循环/恶意代码不会卡死或污染主进程。
   更严格的隔离(容器、文件系统限制)留待正式管线。

用法: python3 scripts/verify_refactory.py <refactory_repo_path>/data/question_1
"""
import sys
import glob
import os
import json
import subprocess
from collections import Counter

PER_PROGRAM_TIMEOUT = 10  # 秒

# 在子进程中执行:读入学生程序与测试用例,输出 JSON 结果
RUNNER = r"""
import sys, json, io, contextlib
prog_path, tests_json = sys.argv[1], sys.argv[2]
tests = json.loads(tests_json)
src = open(prog_path).read()
ns, sink = {}, io.StringIO()
try:
    with contextlib.redirect_stdout(sink):
        exec(src, ns)
except Exception as e:
    print(json.dumps({"passed": 0, "total": len(tests),
                      "mode": "load_error:" + type(e).__name__}))
    sys.exit(0)
passed, fail_mode = 0, None
for expr, expected in tests:
    try:
        with contextlib.redirect_stdout(sink):
            result = eval(expr, ns)
        if str(result) == expected:
            passed += 1
        else:
            fail_mode = fail_mode or "wrong_answer"
    except Exception as e:
        fail_mode = fail_mode or "runtime_error:" + type(e).__name__
print(json.dumps({"passed": passed, "total": len(tests),
                  "mode": fail_mode or "all_passed"}))
"""

def load_tests(qdir):
    tests = []
    for inp in sorted(glob.glob(os.path.join(qdir, "ans", "input_*.txt"))):
        out = inp.replace("input_", "output_")
        with open(inp) as f1, open(out) as f2:
            tests.append((f1.read().strip(), f2.read().strip()))
    return tests

def run_program(path, tests):
    """子进程 + 超时执行单个学生程序。"""
    try:
        proc = subprocess.run(
            [sys.executable, "-c", RUNNER, path, json.dumps(tests)],
            capture_output=True, text=True,
            stdin=subprocess.DEVNULL, timeout=PER_PROGRAM_TIMEOUT)
        return json.loads(proc.stdout.strip().splitlines()[-1])
    except subprocess.TimeoutExpired:
        return {"passed": 0, "total": len(tests), "mode": "timeout"}
    except Exception as e:
        return {"passed": 0, "total": len(tests),
                "mode": f"runner_error:{type(e).__name__}"}

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
    print(f"\n[D 维提交级候选特征] 对前 {len(results)} 个错误程序:")
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
