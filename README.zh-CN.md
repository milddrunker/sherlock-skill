[English](README.md) | **简体中文**

# Sherlock Skill

一个把用户名搜索整理成**有证据、可复核的公开账号地图**的 agent skill。它内置
仅依赖 Python 标准库的扫描器，并附带来自
[Sherlock](https://github.com/sherlock-project/sherlock) 的站点快照，再引导 agent
交叉核验，并在工作区生成结构化报告。

它刻意区分两件事：

```text
账号存在  !=  这些账号属于同一个人
```

Sherlock 提供发现线索；本 skill 增加证据分级、置信度、矛盾处理、隐私最小化和
统一报告格式。

## 生成内容

```text
username_analysis/
└── <安全化后的用户名>/
    ├── username_analysis.md
    ├── evidence.json
    ├── sherlock-scan.json
    ├── sherlock-output.txt
    └── sherlock-error.txt
```

Markdown 报告包括：

- 调查目的、授权依据与范围
- 候选账号 URL 和公开可查事实
- 证据等级和跨平台比对
- `Confirmed` / `Likely` / `Possible` / `Unrelated` / `Inconclusive` 身份判断
- 与调查目的相匹配的公开画像摘要
- 身份与公开活动时间线
- 必须登录或在授权情况下才能确认的信息类别，以及合法确认途径
- 来源、访问日期、限制与后续步骤

skill 指令和默认报告语言均为英文。

## 适用范围

可用于经授权的安全评估、个人账号整理、品牌冒用调查、合法尽职调查，以及已经取得
当事人同意的研究。

本 skill 不用于绕过登录、收集私密数据、窃取凭据或会话、骚扰、定位或联系他人、
冒充身份，也不用于就业、信贷、住房等高风险资格决策。公开可见的信息仍可能敏感，
因此报告遵循最小化原则，并明确区分事实与推断。

## 前置条件

- 已启用 skills 的 Codex
- Python 3.10 或更高版本

不需要通过 `pipx` 或外部命令安装 Sherlock。验证内置站点快照：

```bash
python scripts/sherlock_scan.py validate-data
```

访问目标站点时仍可能需要网络或代理。内置的 481 个站点列表可以复现调查，但可能
旧于上游 Sherlock；如果需要最新站点覆盖，应在报告中记录这一限制。

## 安装 skill

直接把仓库克隆到 Codex skills 目录。

PowerShell：

```powershell
$target = Join-Path $HOME '.codex\skills\sherlock-skill'
git clone https://github.com/milddrunker/sherlock-skill.git $target
```

macOS 或 Linux：

```bash
git clone https://github.com/milddrunker/sherlock-skill.git \
  "${CODEX_HOME:-$HOME/.codex}/skills/sherlock-skill"
```

如果 Codex 没有立即发现 skill，请重启或刷新 Codex。

## 在 Codex 中使用

调用时说明调查目的和授权范围：

```text
使用 $sherlock-skill 调查用户名 "example_user"，用于经授权的品牌冒用
分析，并在当前工作区生成报告。
```

Codex 会运行内置扫描器，查看公开页面，核验账号关联，完成报告并运行
校验器。

## 直接使用辅助脚本

直接运行内置扫描器：

```bash
python scripts/sherlock_scan.py scan \
  --username example_user \
  --output username_analysis/example_user/scan.json
```

创建调查目录：

```bash
python scripts/username_analysis.py collect \
  --username example_user \
  --workspace .
```

如果已经保存了兼容扫描器的输出：

```bash
python scripts/username_analysis.py collect \
  --username example_user \
  --workspace . \
  --from-output sherlock-output.txt
```

校验完成后的报告：

```bash
python scripts/username_analysis.py validate \
  username_analysis/example_user/username_analysis.md
```

查看代理、超时、站点限制和覆盖已有目录等选项：

```bash
python scripts/username_analysis.py collect --help
```

运行仓库测试：

```bash
python -m unittest discover -s tests -v
```

## 证据规则

- 仅有相同用户名属于弱证据。
- 要判断为 `Likely` 同一人，至少需要两个独立且具有辨识度的重合信号，并且没有
  明显矛盾。
- 页面存在、搜索排名和 Sherlock 输出都不能证明账号所有权。
- 页面被拦截、信息过期、账号私密或需要登录时，应记录为限制，不能当成否定结果。
- 登录后才能确认的信息只按类别说明，并给出合法确认途径。skill 不会要求密码、
  Cookie、恢复代码或一次性验证码。

完整的置信度标准和披露规则见
[references/identity-verification.md](references/identity-verification.md)。

## 归属与许可证

本项目独立于 Sherlock 和 OSINTSearch。Sherlock 是由 Siddharth Dushantha 及贡献者
维护的独立 MIT 开源项目。

本仓库采用 [MIT License](LICENSE)。
