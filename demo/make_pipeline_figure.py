"""生成 BRAFAR 五步诊断流水线图(PNG),供 Word 文档嵌入。
用法: python3 demo/make_pipeline_figure.py <输出png路径>
"""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib import font_manager

# 注册中文字体(文泉驿正黑)
FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
font_manager.fontManager.addfont(FONT)
zh = font_manager.FontProperties(fname=FONT)
plt.rcParams["axes.unicode_minus"] = False

steps = [
    ("错误程序 Pb", "输入", "#E8EAF6", "#3949AB"),
    ("Searcher", "找最近参考程序", "#E3F2FD", "#1565C0"),
    ("双向重构", "对齐控制流\n(语义保持)", "#E0F2F1", "#00695C"),
    ("Aligner", "对齐基本块 / 变量", "#FFF3E0", "#E65100"),
    ("Fault Locator", "由粗到细定位可疑块", "#FCE4EC", "#AD1457"),
    ("Repairer", "生成最小补丁", "#F3E5F5", "#6A1B9A"),
    ("修复完成", "通过全部测试", "#E8F5E9", "#2E7D32"),
]

fig, ax = plt.subplots(figsize=(13, 3.2), dpi=170)
ax.set_xlim(0, len(steps) * 2.0)
ax.set_ylim(0.85, 4.35)
ax.axis("off")

box_w, box_h, y = 1.7, 1.15, 2.4
centers = []
for i, (title, sub, fill, edge) in enumerate(steps):
    x = i * 2.0 + 0.15
    cx = x + box_w / 2
    centers.append(cx)
    ax.add_patch(FancyBboxPatch(
        (x, y), box_w, box_h,
        boxstyle="round,pad=0.02,rounding_size=0.12",
        linewidth=2, edgecolor=edge, facecolor=fill))
    ax.text(cx, y + box_h * 0.62, title, ha="center", va="center",
            fontproperties=zh, fontsize=12.5, fontweight="bold", color=edge)
    ax.text(cx, y + box_h * 0.24, sub, ha="center", va="center",
            fontproperties=zh, fontsize=9.2, color="#333333")
    if i < len(steps) - 1:
        nx = (i + 1) * 2.0 + 0.15
        ax.add_patch(FancyArrowPatch(
            (x + box_w, y + box_h / 2), (nx, y + box_h / 2),
            arrowstyle="-|>", mutation_scale=18,
            linewidth=1.8, color="#555555"))

# "定位 + 修复"循环回线:从 Repairer 底部向下绕行,回到 Fault Locator 底部
fl_cx, rp_cx = centers[4], centers[5]
ax.add_patch(FancyArrowPatch(
    (rp_cx, y - 0.05), (fl_cx, y - 0.05),
    connectionstyle="arc3,rad=-0.55", arrowstyle="-|>",
    mutation_scale=16, linewidth=1.8, color="#AD1457", linestyle=(0, (5, 3))))
ax.text((fl_cx + rp_cx) / 2, y - 1.05,
        "定位 + 修复反复循环,直到通过全部测试",
        ha="center", va="top", fontproperties=zh,
        fontsize=9.5, color="#AD1457")

ax.text(centers[0], y + box_h + 0.45,
        "BRAFAR 错误诊断与修复流水线",
        ha="left", va="center", fontproperties=zh,
        fontsize=14, fontweight="bold", color="#1A237E")

plt.tight_layout()
out = sys.argv[1] if len(sys.argv) > 1 else "brafar_pipeline.png"
plt.savefig(out, bbox_inches="tight", facecolor="white")
print("saved:", out)
