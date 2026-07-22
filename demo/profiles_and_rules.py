"""画像、规则与分级话术片段 —— 【黄新意负责填充/打磨】(重做版 v2)

本文件是 demo 的"可替换插槽",黄新意只改这一个文件。三块内容:
  1. PROFILES   3 份模拟画像(四维 K/D/H/E + 说明)
  2. RULES      6 条规则:画像特征 -> 反馈风格四旋钮
  3. 话术片段   开场白 / 定位说法 / 收尾引导(按旋钮取值组织)

v2 相比第一版的变化(房年朗):
  第一版的三段模板把风格"写死"在话术里,四个旋钮算出来却只用了一个。
  v2 把话术拆成按旋钮取值索引的片段,demo.py 负责按旋钮组装 ——
  规则改哪个旋钮,输出就真的变哪里,"画像改变反馈"变得可检验、可解释。

四维画像含义(与申报书一致):
  K 知识基础、D 调试与执行、E 学习演化 —— 取值 low / mid / high
  H 求助与交互 —— 依赖程度 high_dependence / balanced / independent

风格四旋钮(对应 BRAFAR 诊断粒度 -> 反馈强度的映射):
  explain_depth   解释深度: concept(补概念) / step(讲原因) / minimal(不展开)
  code_supply     代码供给: none(不给码) / snippet(给方向) / full_patch(给补丁)
  guide_strength  引导强度: strong(粗定位+反问) / medium(行号+方向) / weak(直给)
  tone            语气:     gentle(鼓励通俗) / neutral(平实) / terse(简洁专业)
"""

# ── 1. 三份模拟画像 ──────────────────────────────────────────────
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

# ── 2. 六条规则:画像特征 -> 风格旋钮 ────────────────────────────
# 每条规则 = (名字, 条件函数, 命中后并入 style 的增量)
RULES = [
    # R1 知识薄弱 → 反馈里要补概念,语气放软
    ("R1_K低_补概念",
     lambda p: p["K"] == "low",
     {"explain_depth": "concept", "tone": "gentle"}),

    # R2 调试能力弱 → 不给代码,粗定位强引导(让他练定位)
    ("R2_D低_不给码强引导",
     lambda p: p["D"] == "low",
     {"code_supply": "none", "guide_strength": "strong"}),

    # R3 高依赖 → 越要答案越不直接给,守住引导(防"拿到代码但没理解")
    ("R3_H高依赖_抵住直给",
     lambda p: p["H"] == "high_dependence",
     {"guide_strength": "strong", "code_supply": "none"}),

    # R4 调试能力中等 → 行号+方向+讲清原因,不给整段
    ("R4_D中_行号加方向",
     lambda p: p["D"] == "mid",
     {"code_supply": "snippet", "guide_strength": "medium",
      "explain_depth": "step"}),

    # R5 调试能力强 → 直接最小补丁,不展开解释
    ("R5_D高_直接补丁",
     lambda p: p["D"] == "high",
     {"code_supply": "full_patch", "guide_strength": "weak",
      "explain_depth": "minimal", "tone": "terse"}),

    # R6 演化良好 → 语气可以更简,减少重复叮嘱
    ("R6_E高_从简",
     lambda p: p["E"] == "high",
     {"tone": "terse"}),
]

# 默认风格(规则都没命中时的兜底)
DEFAULT_STYLE = {
    "explain_depth": "step",
    "code_supply": "snippet",
    "guide_strength": "medium",
    "tone": "neutral",
}

# ── 3. 分级话术片段(黄新意打磨文字;键 = 旋钮取值)──────────────
# 开场白:按语气
OPENINGS = {
    "gentle": "别急,这个错误很多同学都会遇到,我们一步步来 🙂",
    "neutral": "运行没有全部通过,来看一下问题。",
    "terse": "",  # 简洁风格不放开场白
}

# 定位说法:按引导强度(对应 BRAFAR 由粗到细的定位深度)
#   strong -> 只给粗粒度区域(复合块级),让学习者自己缩小范围
#   medium -> 给到行号(基本块/语句级)
#   weak   -> 行号 + 最小改法(补丁级)
def locate_strong(diag):
    return (f"问题出在「{diag['fault_region']}」附近,类型是"
            f"{diag['error_class']}。先自己找找具体是哪一行。")

def locate_medium(diag):
    return f"问题在第 {diag['fault_line']} 行,类型是{diag['error_class']}。"

def locate_weak(diag):
    return f"第 {diag['fault_line']} 行:{diag['min_fix_hint']}。"

LOCATION = {"strong": locate_strong, "medium": locate_medium, "weak": locate_weak}

# 收尾引导:按引导强度
CLOSINGS = {
    "strong": "想一想:这一行在什么输入下会得到不符合预期的结果?"
              "自己改一版,跑一遍测试再看。",
    "medium": "按这个方向自己改改看,并想想为什么这样能覆盖漏掉的情况。",
    "weak": "",  # 直给档不需要引导语
}
