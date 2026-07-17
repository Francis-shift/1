# 数据层验证脚本使用说明

配套文档:`docs/第一周任务-候选数据资源清单与初步判断.md` 第六节。

## 环境要求

- Python 3.11+(实测 3.11.15,Ubuntu 24.04)
- 验证脚本本身**只用标准库**,无需安装任何依赖
- 运行 BRAFAR 工具才需要装依赖(见下文第 3 节)

## 1. Refactory 验证(D 维提交级候选特征)

```bash
# 获取数据(约 3.5MB 仓库 + 解压后数据)
git clone --depth 1 https://github.com/githubhuyang/refactory.git
cd refactory && unzip data.zip && cd ..

# 运行验证(默认取前 100 个错误程序)
python3 scripts/verify_refactory.py refactory/data/question_1
```

预期输出:规模核对(reference 1 / correct 768 / wrong 575 / 测试 11 个)、
参考程序 11/11 通过、100 个错误程序的通过率与失败模式分布,
并把逐程序特征写入 `scripts/output_refactory_features.json`(库内已有一份示例输出)。

安全机制:每个学生程序在独立子进程执行,stdin 关闭,单程序超时 10 秒;
死循环程序会记为 `timeout` 而不会卡死脚本。

## 2. CS1QA 验证(H 维候选特征)

```bash
# 获取数据(仓库约 282MB,含 71MB 聊天 JSON)
git clone --depth 1 https://github.com/cyoon47/cs1qa.git

# 运行验证
python3 scripts/verify_cs1qa.py cs1qa
```

预期输出:标注集 9237 条(train 5543 / dev 1847 / test 1847,与论文一致)、
真实字段清单、9 类问题类型分布、17698 个会话 / 1317 名学生的
求助频率与消息轮次统计,以及按学生聚合的 H 维候选特征示例。

注意:学生**代码**全量数据不在 GitHub,需邮件 changyoon.lee@kaist.ac.kr。

## 3. BRAFAR 烟雾测试(修复工具可用性)

```bash
git clone --depth 1 https://github.com/LinnaX7/brafar-python.git
cd brafar-python && unzip data.zip

# 依赖是老包,新版 setuptools 编译失败,必须先降级(实测可行的组合):
python3 -m venv venv
venv/bin/pip install "setuptools==59.8.0" wheel
venv/bin/pip install -r requirements.txt

# 构造迷你数据集(把 data/question_1 里 wrong 只留几个)后运行:
venv/bin/python run.py -d ./minidata -q question_1 -s 0
# 输出:minidata/question_1/brafar_result_0.csv(含修复代码、RPS、耗时)
```

`-s 0` 表示只用教师参考程序作修复源(最快);跑全量 575 个错误程序
直接把 `-d` 指向解压出的 `./data` 即可,耗时约几分钟。

## 数据集落盘位置约定

数据集体积较大且许可各异,**不要提交进本仓库**;克隆到仓库外的
临时/数据目录,脚本以路径参数传入。
