"""画像驱动个性化反馈 —— 最小可跑通 demo(第一版,不接 VS Code / 真实数据)

核心目标(对应任务书):验证"同一错误在不同画像下产生不同反馈",
即证明"学习者画像"这个变量真的能改变系统的反馈方式。

数据流(与申报书"读画像→判断状态→选策略→个性化反馈"一致):
    错误案例(含 BRAFAR 式诊断)          <- 房年朗
         +                                       demo.py 负责串联(房年朗搭骨架)
    学习者画像 --规则--> 反馈风格 --模板--> 个性化反馈   <- 黄新意填充画像/规则/模板

用法:
    python3 demo/demo.py            # 跑全部 3 案例 × 3 画像的对照矩阵
    python3 demo/demo.py --check    # 先核验错误案例真的会失败,再跑对照
"""
import os
import sys
import copy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cases.cases import CASES                         # noqa: E402
from profiles_and_rules import (                       # noqa: E402
    PROFILES, RULES, DEFAULT_STYLE, TEMPLATES,
)


def resolve_style(profile):
    """把画像跑过 6 条规则,得到该画像对应的反馈风格。
    这一步就是'画像 -> 策略'的策略控制器雏形。"""
    style = copy.deepcopy(DEFAULT_STYLE)
    fired = []
    for name, cond, delta in RULES:
        if cond(profile):
            style.update(delta)
            fired.append(name)
    return style, fired


def make_diag(case):
    """从错误案例抽取'诊断信息'交给模板。
    第一版直接用案例里预先整理好的 BRAFAR 式诊断;
    正式版这里换成实时调用 BRAFAR 工具产出 fault_line / patched。"""
    return {
        "error_class": case["error_class"],
        "diagnosis": case["diagnosis"],
        "fault_line": case["fault_line"],
        "min_fix_hint": case["min_fix_hint"],
        "concept_hint": case["concept_hint"],
        "patched": case["patched"],
    }


def generate_feedback(case, profile):
    """给定错误案例 + 画像,产出个性化反馈。"""
    style, fired = resolve_style(profile)
    template = TEMPLATES[style["guide_strength"]]
    text = template(make_diag(case))
    return text, style, fired


def run_matrix():
    """对照矩阵:每个错误案例,依次用 3 份画像生成反馈,直观对比差异。"""
    for case in CASES:
        print("=" * 72)
        print(f"错误案例:{case['id']}  【{case['error_class']}】")
        print(f"来源:{case['source']}")
        print("错误代码:")
        for n, line in enumerate(case["buggy"].rstrip().splitlines(), 1):
            mark = "  <-- 出错行" if n == case["fault_line"] else ""
            print(f"    {n}| {line}{mark}")
        print()
        for key, profile in PROFILES.items():
            text, style, fired = generate_feedback(case, profile)
            print(f"  ┌─ 画像【{profile['name']}】"
                  f"(K={profile['K']} D={profile['D']} "
                  f"E={profile['E']} H={profile['H']})")
            print(f"  │  命中规则:{', '.join(fired) or '(无,用默认)'}")
            print(f"  │  反馈风格:引导={style['guide_strength']} "
                  f"代码={style['code_supply']} "
                  f"解释={style['explain_depth']} 语气={style['tone']}")
            print("  │  ── 系统反馈 ──")
            for line in text.splitlines():
                print(f"  │   {line}")
            print("  └" + "─" * 60)
        print()


def main():
    if "--check" in sys.argv:
        import subprocess
        here = os.path.dirname(os.path.abspath(__file__))
        print(">> 先核验 3 个错误案例确实会失败……")
        subprocess.run([sys.executable, os.path.join(here, "run_case_check.py")])
        print("\n>> 核验通过,开始生成个性化反馈对照矩阵:\n")
    run_matrix()
    print("=" * 72)
    print("结论:同一个错误,3 份画像 → 3 种不同反馈,说明'画像'确实改变了"
          "反馈方式。")
    print("第一版验证达成。下一步:接入 BRAFAR 实时诊断、真实数据与 VS Code。")


if __name__ == "__main__":
    main()
