"""画像驱动个性化反馈 —— 最小可跑通 demo(重做版 v2,不接 VS Code / 真实数据)

核心目标(对应任务书):验证"同一错误在不同画像下产生不同反馈",
即证明"学习者画像"这个变量真的能改变系统的反馈方式。

数据流(与申报书"读画像→判断状态→选策略→个性化反馈"一致):
    错误案例(含 BRAFAR 式诊断包)                    <- 房年朗
        +                                             demo.py 组装(房年朗骨架)
    画像 --6条规则--> 风格四旋钮 --话术片段--> 个性化反馈  <- 黄新意填充

v2 相比第一版的变化:
  反馈由"三段写死的模板"改为**按四个旋钮组装**:
    定位深度(guide_strength:粗区域/行号/行号+改法,对应 BRAFAR 由粗到细)
    解释深度(explain_depth:补概念/讲原因/不展开)
    代码供给(code_supply:不给/给方向/给补丁)
    语气(tone:开场白与收尾的措辞)
  并在结尾**机器校验**:每个案例的 3 份反馈两两不同,验证结论不靠肉眼。

用法:
    python3 demo/demo.py            # 3 案例 × 3 画像 对照矩阵 + 差异校验
    python3 demo/demo.py --check    # 先核验错误案例确实失败,再跑对照
"""
import os
import sys
import copy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cases.cases import CASES                          # noqa: E402
from profiles_and_rules import (                        # noqa: E402
    PROFILES, RULES, DEFAULT_STYLE, OPENINGS, LOCATION, CLOSINGS,
)


def resolve_style(profile):
    """画像跑过 6 条规则 -> 该画像的反馈风格(策略控制器雏形)。"""
    style = copy.deepcopy(DEFAULT_STYLE)
    fired = []
    for name, cond, delta in RULES:
        if cond(profile):
            style.update(delta)
            fired.append(name)
    return style, fired


def make_diag(case):
    """从错误案例抽取诊断包(第一版为预整理;正式版换成实时调用 BRAFAR)。"""
    return {k: case[k] for k in (
        "error_class", "diagnosis", "fault_line", "fault_region",
        "min_fix_hint", "concept_hint", "patched")}


def compose_feedback(diag, style):
    """按风格四旋钮组装反馈 —— 每个旋钮都真实改变输出的对应部分。"""
    parts = []

    # ① 开场白:由 tone 决定
    if OPENINGS[style["tone"]]:
        parts.append(OPENINGS[style["tone"]])

    # ② 定位:由 guide_strength 决定深度(粗区域 / 行号 / 行号+改法)
    parts.append(LOCATION[style["guide_strength"]](diag))

    # ③ 解释:由 explain_depth 决定给什么
    if style["explain_depth"] == "concept":
        parts.append(f"相关概念:{diag['concept_hint']}")
    elif style["explain_depth"] == "step":
        parts.append(f"原因:{diag['diagnosis']}")
    # minimal:不追加解释

    # ④ 代码:由 code_supply 决定给多少
    if style["code_supply"] == "snippet":
        parts.append(f"修改方向:{diag['min_fix_hint']}(先不给完整代码)")
    elif style["code_supply"] == "full_patch":
        parts.append("最小修复后:\n" + diag["patched"])
    # none:不给任何代码

    # ⑤ 收尾:由 guide_strength 决定引导语
    if CLOSINGS[style["guide_strength"]]:
        parts.append(CLOSINGS[style["guide_strength"]])

    return "\n".join(parts)


def generate_feedback(case, profile):
    style, fired = resolve_style(profile)
    return compose_feedback(make_diag(case), style), style, fired


def run_matrix():
    """对照矩阵 + 差异机器校验。返回是否全部案例的反馈两两不同。"""
    all_distinct = True
    for case in CASES:
        print("=" * 72)
        print(f"错误案例:{case['id']}  【{case['error_class']}】")
        print(f"来源:{case['source']}")
        print("错误代码:")
        for n, line in enumerate(case["buggy"].rstrip().splitlines(), 1):
            mark = "  <-- 出错行" if n == case["fault_line"] else ""
            print(f"    {n}| {line}{mark}")
        print()
        texts = []
        for key, profile in PROFILES.items():
            text, style, fired = generate_feedback(case, profile)
            texts.append(text)
            print(f"  ┌─ 画像【{profile['name']}】"
                  f"(K={profile['K']} D={profile['D']} "
                  f"E={profile['E']} H={profile['H']})")
            print(f"  │  命中规则:{', '.join(fired) or '(无,用默认)'}")
            print(f"  │  风格旋钮:定位深度={style['guide_strength']} "
                  f"解释={style['explain_depth']} "
                  f"代码={style['code_supply']} 语气={style['tone']}")
            print("  │  ── 系统反馈 ──")
            for line in text.splitlines():
                print(f"  │   {line}")
            print("  └" + "─" * 60)
        distinct = len(set(texts)) == len(texts)
        all_distinct = all_distinct and distinct
        print(f"  [校验] 本案例 3 份反馈两两不同:{'✓' if distinct else '✗'}")
        print()
    return all_distinct


def main():
    if "--check" in sys.argv:
        import subprocess
        here = os.path.dirname(os.path.abspath(__file__))
        print(">> 先核验 3 个错误案例确实会失败……")
        r = subprocess.run([sys.executable,
                            os.path.join(here, "run_case_check.py")])
        if r.returncode != 0:
            print("案例核验失败,终止。")
            sys.exit(1)
        print("\n>> 核验通过,生成个性化反馈对照矩阵:\n")
    ok = run_matrix()
    print("=" * 72)
    if ok:
        print("结论(机器校验通过):同一错误,3 份画像 → 3 份两两不同的反馈,")
        print("且差异可解释(每处差异都能追溯到命中的规则与旋钮)。第一版验证达成。")
    else:
        print("警告:存在案例的不同画像产生了相同反馈,规则或话术需要调整!")
    print("下一步:接入 BRAFAR 实时诊断、真实行为数据与 VS Code。")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
