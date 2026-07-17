"""数据层验证脚本 2:CS1QA(求助与交互数据)

验证内容:
1. 标注数据(data/final/cleaned/equal/*.jsonl)的真实字段与规模
2. 未标注聊天(data/chat_cleaned.json)的真实字段与规模
3. 产出 H 维(求助与交互)候选特征示例:
   - 问题类型分布(questionType)
   - 学生主动提问 vs 助教发起 的比例(questioner)
   - 按学生聚合:观察期内会话总数、每会话平均消息数(含双方)、
     每会话学生侧消息数(追问轮次的近似上界)
     —— CS1QA 含匿名学生 ID,可按学生聚合,是最接近
     "每个学习者一份 user profile"的公开数据。

口径说明:
 - "每会话平均消息数"统计 comments 全部消息(学生 + 助教),不等于追问深度;
 - "学生侧消息数"只数 user_id == student_user_id 的消息,可视为
   学生提问/追问轮次的近似(仍含粘贴代码等非提问消息,属上界);
 - "人均会话数"是整个数据集观察期(约一学期)内的总数,不是每周频率。

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

    per_student = defaultdict(lambda: {"sessions": 0, "msgs": 0, "stu_msgs": 0})
    for c in chats:
        sid = c.get("student_user_id")
        comments = c.get("comments") or []
        per_student[sid]["sessions"] += 1
        per_student[sid]["msgs"] += len(comments)
        per_student[sid]["stu_msgs"] += sum(
            1 for m in comments if m.get("user_id") == sid)

    n_students = len(per_student)
    sess = [v["sessions"] for v in per_student.values()]
    msgs = [v["msgs"] / v["sessions"] for v in per_student.values()]
    stu = [v["stu_msgs"] / v["sessions"] for v in per_student.values()]
    print(f"  覆盖学生数: {n_students}")
    print(f"  人均求助会话数(整个观察期): {sum(sess)/n_students:.1f}(最多 {max(sess)})")
    print(f"  每会话平均消息数(含学生与助教双方): {sum(msgs)/n_students:.1f}")
    print(f"  每会话学生侧消息数(追问轮次近似上界): {sum(stu)/n_students:.1f}")

    print(f"\n[H 维候选特征示例] 求助最频繁的 {top_n} 名学生(匿名 ID):")
    ranked = sorted(per_student.items(), key=lambda kv: -kv[1]["sessions"])
    for sid, v in ranked[:top_n]:
        print(f"    student_{sid}: 观察期求助 {v['sessions']} 次,"
              f"每会话学生侧消息 {v['stu_msgs']/v['sessions']:.1f} 条"
              f" -> 候选 H 维'求助频率/交互密度'特征")

if __name__ == "__main__":
    repo = sys.argv[1]
    verify_labeled(repo)
    verify_chat(repo)
