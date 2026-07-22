"""画像、规则与分级反馈模板 —— 【黄新意负责填充】

本文件是 demo 的"可替换插槽"。房年朗已把结构和一份**示例填充**写好,
黄新意需要做的是:
  1. 核定/改写 3 份模拟画像 PROFILES(四维 K/D/H/E + 水平标签)
  2. 筛选/改写 6 条规则 RULES(画像特征 -> 反馈风格参数)
  3. 打磨 3 档分级反馈模板 TEMPLATES(新手/进阶/熟练三档的话术)

下面的内容是房年朗给的**初稿示例**,保证 demo 能跑;黄新意可直接在原处修改。
四维画像含义(与申报书一致):
  K 知识基础、D 调试与执行、E 学习演化 —— 取值 low / mid / high
  H 求助与交互 —— 依赖程度 high_dependence / balanced / independent
"""

# ── 1. 三份模拟画像(黄新意可调整取值与命名)──────────────────────
PROFILES = {
    "novice": {
        "name": "新手型 · 小 A",
        "K": "low", "D": "low", "E": "low", "H": "high_dependence",
        "note": "语法/概念尚不牢,报错后容易乱改,倾向直接要完整答案",
    },
    "intermediate": {
        "name": "进阶型 · 小 B",
        "K": "mid", "D": "mid", "E": "mid", "H": "balanced",
        "note": "能读懂大部分报错,愿意自己试,需要方向性提示",
    },
    "proficient": {
        "name": "熟练型 · 小 C",
        "K": "high", "D": "high", "E": "high", "H": "independent",
        "note": "定位能力强,只想要关键差异和最小补丁,讨厌啰嗦",
    },
}

# ── 2. 六条规则:画像特征 -> 反馈风格 ────────────────────────────
# 每条规则是 (条件函数, 风格增量) ;命中即把增量并入 style。
# 风格四个旋钮(对应 BRAFAR 诊断粒度 -> 反馈强度的映射):
#   explain_depth   解释粒度: concept(补概念) / step(讲步骤) / minimal(只点关键)
#   code_supply     代码供给: none(不给码) / snippet(局部) / full_patch(完整补丁)
#   guide_strength  引导强度: strong(强引导,多问少答) / medium / weak(直给)
#   tone            语言风格: gentle(通俗鼓励) / neutral / terse(简洁专业)
RULES = [
    ("K_low_needs_concept",
     lambda p: p["K"] == "low",
     {"explain_depth": "concept", "tone": "gentle"}),

    ("D_low_no_full_code",
     lambda p: p["D"] == "low",
     {"code_supply": "none", "guide_strength": "strong"}),

    ("H_dependence_resist_answer",
     lambda p: p["H"] == "high_dependence",
     {"guide_strength": "strong"}),  # 越依赖越不能直接喂答案,反而强引导

    ("D_mid_give_hint",
     lambda p: p["D"] == "mid",
     {"code_supply": "snippet", "guide_strength": "medium",
      "explain_depth": "step"}),

    ("D_high_give_patch",
     lambda p: p["D"] == "high",
     {"code_supply": "full_patch", "guide_strength": "weak",
      "explain_depth": "minimal", "tone": "terse"}),

    ("E_high_can_be_brief",
     lambda p: p["E"] == "high",
     {"tone": "terse"}),
]

# 默认风格(所有规则都没命中时的兜底)
DEFAULT_STYLE = {
    "explain_depth": "step",
    "code_supply": "snippet",
    "guide_strength": "medium",
    "tone": "neutral",
}

# ── 3. 三档分级反馈模板(黄新意打磨话术)────────────────────────
# 模板按 guide_strength 选档;用诊断信息 diag 填空。
# diag 字段来自错误案例:error_class / diagnosis / fault_line / min_fix_hint / patched
def template_strong(diag):
    """新手档:补概念、只给方向和提示,绝不直接给答案。"""
    return (
        f"先别急着改代码,我们一起想一想 🙂\n"
        f"你的程序在「{diag['error_class']}」上出了问题。\n"
        f"提示:注意第 {diag['fault_line']} 行附近——"
        f"{diag['concept_hint']}\n"
        f"你可以先问自己:这一行在什么情况下会得到不符合预期的结果?"
        f"想清楚后自己改改看,改完再运行测试。"
    )

def template_medium(diag):
    """进阶档:指出位置 + 给方向性提示 + 局部片段,不给完整答案。"""
    return (
        f"问题出在第 {diag['fault_line']} 行:{diag['diagnosis']}\n"
        f"修改方向:{diag['min_fix_hint']}。\n"
        f"你先按这个方向试,想想为什么这样改能覆盖之前漏掉的情况。"
    )

def template_weak(diag):
    """熟练档:直接给最小补丁 + 一句关键差异,简洁。"""
    return (
        f"第 {diag['fault_line']} 行:{diag['min_fix_hint']}。\n"
        f"最小修复后:\n{diag['patched']}"
    )

TEMPLATES = {
    "strong": template_strong,
    "medium": template_medium,
    "weak": template_weak,
}
