"""数据层验证脚本 2:CS1QA(求助与交互数据)

验证内容:
1. 标注数据(data/final/cleaned/equal/*.jsonl)的真实字段与规模
2. 未标注聊天(data/chat_cleaned.json)的真实字段与规模
3. 产出 H 维(求助与交互)画像特征示例:
   - 问题类型分布(questionType)
   - 学生主动提问 vs 助教发起 的比例(questioner)
   - 按学生聚合的求助频率与追问深度(会话消息轮次)
     —— 即"每个学习者一份"的 H 维特征雏形。

用法: python3 scripts/verify_cs1qa.py <cs1qa_repo_path>
"""
import sys
import os
import json
import glob
from collections import Counter, defaultdict

def verify_labeled(repo):
    base = os.path.join(repo, "data", "final", "cleaned", "equal")
    splits = ["train_cleaned.jsonl", "dev_cleaned.jsonl", "test_cleaned.jsonl"]
    total, qtypes, questioners = 0, Counter(), Counter()
    fields = None
    for name in splits:
        with open(os.path.join(base, name)) as f:
            for line in f:
                d = json.loads(line)
                fields = fields or list(d.keys())
                total += 1
                qtypes[d.get("questionType")] += 1
                questioners[d.get("questioner")] += 1
    n_aug = sum(1 for _ in open(os.path.join(base, "augmented_train_cleaned.jsonl")))
    print(f"[标注数据] train+dev+test 共 {total} 条问答对(论文口径 9237),"
          f"另有增强训练集 {n_aug} 条")
    print(f"  真实字段: {fields}")
    print(f"  问题类型分布(H 维特征之一): {dict(qtypes.most_common())}")
    print(f"  提问者分布: {dict(questioners)}")

def verify_chat(repo, top_n=5):
    p = os.path.join(repo, "data", "chat_cleaned.json")
    with open(p) as f:
        chats = json.load(f)
    print(f"\n[未标注聊天] {len(chats)} 个会话")
    print(f"  会话级字段: {list(chats[0].keys())}")

    per_student = defaultdict(lambda: {"sessions": 0, "msgs": 0})
    for c in chats:
        sid = c.get("student_user_id")
        n_msg = len(c.get("comments") or [])
        per_student[sid]["sessions"] += 1
        per_student[sid]["msgs"] += n_msg

    n_students = len(per_student)
    sess = [v["sessions"] for v in per_student.values()]
    depth = [v["msgs"] / v["sessions"] for v in per_student.values()]
    print(f"  覆盖学生数: {n_students}")
    print(f"  人均求助会话数: {sum(sess)/n_students:.1f}(最多 {max(sess)})")
    print(f"  人均每会话消息轮次(追问深度): {sum(depth)/n_students:.1f}")

    print(f"\n[H 维特征示例] 求助最频繁的 {top_n} 名学生(匿名 ID):")
    ranked = sorted(per_student.items(), key=lambda kv: -kv[1]["sessions"])
    for sid, v in ranked[:top_n]:
        print(f"    student_{sid}: 求助 {v['sessions']} 次,"
              f"平均追问深度 {v['msgs']/v['sessions']:.1f} 轮"
              f" -> 可映射为 H 维'求助频率/依赖度'标签")

if __name__ == "__main__":
    repo = sys.argv[1]
    verify_labeled(repo)
    verify_chat(repo)
