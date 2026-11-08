[English](README.md) | **简体中文**

# Sherlock Skill

**把用户名搜索线索整理成有证据、可复核的调查报告。**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Runtime dependencies: 0](https://img.shields.io/badge/runtime_dependencies-0-brightgreen.svg)](#前置条件)

Sherlock Skill 面向安全研究人员、品牌保护团队和 AI Agent，提供一套公开信息
调查工作流。它内置用户名扫描器，并规范候选复核、有限线索发现、身份关联判断和
报告校验。

普通用户名扫描只能回答“这个账号名是否出现在某个站点”；本项目进一步处理：

> 这些账号之间是否有证据支持同一人判断，证据强度如何？

## 项目说明

用户名扫描器能够提供有效线索，但匹配到的 URL 列表并不等于完整调查。页面可能
属于其他人、已经过期、处于私密状态、被平台拦截，或由不同的人控制。

本项目补充了可重复公开信息调查所需的能力：

- 明确区分可观察事实与推断
- 使用证据等级和置信度表达结论
- 仅从有辨识度的公开线索开展有限轮次追踪
- 记录矛盾、死路和访问失败，而不是只保留有利结果
- 遵循隐私最小化原则，限制敏感信息输出
- 生成统一 Markdown 报告和机器可读证据
- 校验未完成报告和未替换的模板内容

仓库内置扫描器，不依赖外部 `sherlock` 命令、`pipx`、API Key 或第三方 Python
包。

## 核心能力

- **适配 Agent 工作流：** `SKILL.md` 定义了可供任意 Agent 读取和执行的复核与
  报告流程。
- **有限线索追踪：** 默认最多增加两轮衍生搜索和 12 次线索检查。
- **身份关联约束：** 相同用户名、显示名或搜索结果本身不能证明账号属于同一人。
- **整合式报告：** 区分有证据支持的账号簇与未归属候选，并保留失败和被拦截的
  检查。
- **本地执行：** 扫描器仅使用 Python 标准库。
- **结果可审计：** 报告同时记录来源 URL、访问日期、置信度和调查限制。

## 快速开始

### 前置条件

- Python 3.10 或更高版本
- Windows、macOS 或 Linux
- 可访问待调查站点的网络

### 创建调查案例

```bash
git clone https://github.com/milddrunker/sherlock-skill.git
cd sherlock-skill

python scripts/username_analysis.py collect \
  --username example_user \
  --workspace .
```

工具会扫描内置站点列表，并创建：

```text
username_analysis/example_user/
├── username_analysis.md
├── evidence.json
├── sherlock-scan.json
├── sherlock-output.txt
└── sherlock-error.txt
```

可使用 `--site` 限制调查范围，使用 `--timeout` 降低请求压力：

```bash
python scripts/username_analysis.py collect \
  --username example_user \
  --workspace . \
  --site GitHub \
  --site Gitee \
  --timeout 10
```

代理、并发数、NSFW 站点和覆盖已有目录等选项可通过以下命令查看：

```bash
python scripts/username_analysis.py collect --help
```

### 仅运行扫描器

```bash
python scripts/sherlock_scan.py scan \
  --username example_user \
  --output username_analysis/example_user/scan.json
```

### 校验完成的报告

```bash
python scripts/username_analysis.py validate \
  username_analysis/example_user/username_analysis.md
```

## 配合 Agent 使用

向 Agent 提供 skill 路径、调查目的和范围：

```text
读取 /path/to/sherlock-skill/SKILL.md。调查用户名 "example_user"，用于经授权的
品牌冒用分析。复核所有公开候选，在规则允许的范围内追查独特公开线索，完成报告并
运行校验器。
```

Agent 需要区分发现线索和身份证据，避免收集私密或需要登录的信息，并保留归属
不明的候选。

## 证据标准

| 结论 | 最低标准 |
|---|---|
| Confirmed | 账号本人直接公开声明或双向链接直接且唯一地关联账号 |
| Likely | 至少两个独立、具有辨识度的重合信号，且没有实质矛盾 |
| Possible | 一个弱到中等强度信号，且没有矛盾 |
| Unrelated | 有证据表明属于不同人或存在互不兼容的事实 |
| Inconclusive | 证据不足、无法访问、已经过期或仍有歧义 |

页面存在、搜索排名和扫描器输出都只是发现信号，不能证明账号所有权。完整标准见
[identity-verification.md](references/identity-verification.md)，有限追踪流程见
[pivot-discovery.md](references/pivot-discovery.md)。

## 安全与隐私

仅在有合法依据和适当授权范围时使用本项目开展公开信息调查。典型用途包括经授权的
安全评估、个人账号整理、品牌冒用调查、合法尽职调查，以及取得当事人同意的研究。

本项目不是人员定位工具，也不能确认法律身份。不得用于绕过身份验证、收集私密数据、
窃取凭据或会话、骚扰或定位他人、冒充身份，或作出就业、信贷、住房等高风险资格
决定。

请勿在公开 Issue 中提交凭据、私密调查数据或敏感个人信息。公开可见的信息仍可能
涉及隐私，本项目要求只保留调查所需的最少事实。

## 兼容性与限制

- 需要 Python 3.10 或更高版本。
- 扫描依赖公开端点，可能遇到 CAPTCHA、WAF、限流，或只能通过浏览器读取的客户端
  页面。
- 内置的 481 个站点快照可以复现调查，但可能旧于上游 Sherlock；需要最新覆盖时
  应在报告中记录这一限制。
- 扫描结果只是候选账号，不代表已经确认账号所有权。
- 报告校验器检查结构、必填结论、置信度和未完成模板；通过校验不等于分析结论一定
  正确。

## 开发

运行测试并验证内置站点数据：

```bash
python -m unittest discover -s tests -v
python scripts/sherlock_scan.py validate-data
```

欢迎提交范围明确的 Bug 报告和 Pull Request。所有改动都应遵守公开信息与隐私边界。

## 文档

- [Agent 工作流](SKILL.md)
- [跨宿主命令接口](AGENTS.md)
- [程序化清单](agent-manifest.json)
- [身份核验规则](references/identity-verification.md)
- [有限线索追踪](references/pivot-discovery.md)

## 许可证

本项目独立维护，不是 Sherlock Project 的官方发布版本。本项目采用
[MIT License](LICENSE)。第三方数据及许可证声明见
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
