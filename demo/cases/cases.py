"""3 个 Python 错误案例(房年朗负责的交付物之一)

任务:Sequential Search —— 输入值 x 与已排序序列 seq,返回 x 应插入的位置
      (使序列保持有序);等价于"seq 中有多少个元素小于 x"。
参考正确实现(reference):
    def search(x, seq):
        for i in range(len(seq)):
            if x <= seq[i]:
                return i
        return len(seq)

三个案例均取自 Refactory 公开数据集 question_1 的真实学生错误程序
(github.com/githubhuyang/refactory),不是人工杜撰,已用测试用例复现其失败。
每个案例覆盖一类典型错误,对应 BRAFAR 故障定位的不同难度,也对应
后续画像分级反馈的不同讲法。
"""

# 参考正确程序(BRAFAR 里的 P_c;demo 里既用于对照,也用于自动判分)
REFERENCE = '''\
def search(x, seq):
    for i in range(len(seq)):
        if x <= seq[i]:
            return i
    return len(seq)
'''

# 每个案例:错误代码 buggy、错误类别、一句话诊断、出错行、
# 以及一组测试用例(输入实参元组 -> 期望返回值)
CASES = [
    {
        "id": "case1_boundary",
        "source": "Refactory question_1 / wrong_1_001.py",
        "error_class": "边界条件错误(逻辑错,答案错误)",
        "buggy": '''\
def search(x, seq):
    for i, e in enumerate(seq):
        if x < e:
            return i
    return len(seq)
''',
        "diagnosis": "比较用了严格小于 `x < e`,漏掉了 x 等于当前元素的情况;"
                     "题目要求 x 等于某元素时也应停在该位置,应为 `x <= e`。",
        "fault_line": 3,          # if x < e:
        "fault_region": "循环里的比较判断",   # 粗粒度定位(BRAFAR 复合块级)
        "min_fix_hint": "`<` 改为 `<=`",
        "concept_hint": "「严格小于 <」和「小于等于 <=」在边界(相等)时行为不同,"
                        "查找类问题要特别小心 = 这个临界点。",
        "patched": "def search(x, seq):\n    for i, e in enumerate(seq):\n"
                   "        if x <= e:\n            return i\n    return len(seq)",
        "tests": [
            ((3, (1, 3, 5)), 1),      # x 恰好等于中间元素 -> 暴露边界错
            ((0, (1, 2, 3)), 0),
            ((10, (1, 2, 3)), 3),
            ((2, (1, 3, 5)), 1),
        ],
    },
    {
        "id": "case2_unbound",
        "source": "Refactory question_1 / wrong_1_002.py",
        "error_class": "变量未定义 / 空序列边界(运行时错误 UnboundLocalError)",
        "buggy": '''\
def search(x, seq):
    for i in range(len(seq)):
        if x <= seq[i]:
            return i
    return i + 1
''',
        "diagnosis": "循环没命中时用 `return i + 1`,但当 seq 为空时循环体从未执行,"
                     "变量 i 从未被赋值,触发 UnboundLocalError;"
                     "且非空时正确的兜底应是 `len(seq)` 而不是 `i + 1`。",
        "fault_line": 5,          # return i + 1
        "fault_region": "循环结束之后的返回语句",  # 粗粒度定位(BRAFAR 复合块级)
        "min_fix_hint": "`return i + 1` 改为 `return len(seq)`",
        "concept_hint": "循环里定义的变量,在循环一次都没执行时是「不存在」的;"
                        "依赖循环变量做兜底返回是危险的,应改用与循环无关的量。",
        "patched": "def search(x, seq):\n    for i in range(len(seq)):\n"
                   "        if x <= seq[i]:\n            return i\n    return len(seq)",
        "tests": [
            ((1, ()), 0),             # 空序列 -> 暴露 UnboundLocalError
            ((5, (1, 2, 3)), 3),      # 循环未命中 -> 暴露 i+1 兜底错
            ((2, (1, 3, 5)), 1),
            ((1, (1, 2, 3)), 0),
        ],
    },
    {
        "id": "case3_indexerror",
        "source": "Refactory question_1 / wrong_1_004.py",
        "error_class": "空序列下标越界(运行时错误 IndexError)",
        "buggy": '''\
def search(x, seq):
    if x < seq[0]:
        return 0
    elif x > seq[-1]:
        return len(seq)
    else:
        seq_enum = [i for i in enumerate(seq)]
        for j in range(len(seq_enum) - 1):
            if x >= seq_enum[j][1] and x <= seq_enum[j + 1][1]:
                return j + 1
''',
        "diagnosis": "一上来就访问 `seq[0]` 和 `seq[-1]`,没有先处理空序列,"
                     "空序列时立即 IndexError;整体思路(分三段判断)也比参考实现"
                     "复杂、易漏边界,BRAFAR 会先做结构对齐再定位。",
        "fault_line": 2,          # if x < seq[0]:
        "fault_region": "函数开头对序列的下标访问",  # 粗粒度定位(BRAFAR 复合块级)
        "min_fix_hint": "进入下标访问前先判空:`if not seq: return 0`",
        "concept_hint": "用下标或 seq[0]/seq[-1] 访问序列前,必须先确认它非空;"
                        "空序列是最常见、最容易被忽略的边界。",
        "patched": "def search(x, seq):\n    if not seq:\n        return 0\n"
                   "    if x < seq[0]:\n        return 0\n    elif x > seq[-1]:\n"
                   "        return len(seq)\n    else:\n"
                   "        seq_enum = [i for i in enumerate(seq)]\n"
                   "        for j in range(len(seq_enum) - 1):\n"
                   "            if x >= seq_enum[j][1] and x <= seq_enum[j + 1][1]:\n"
                   "                return j + 1",
        "tests": [
            ((1, ()), 0),             # 空序列 -> 暴露 IndexError
            ((3, (1, 3, 5)), 1),
            ((0, (1, 2, 3)), 0),
            ((10, (1, 2, 3)), 3),
        ],
    },
]
