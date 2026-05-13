# SkillHub 发布指南

> 从本技能发布过程中总结的经验

## 前置条件

1. **GitHub 账号** — 必须有 GitHub repo 才能发布到 SkillHub
2. **GitHub CLI 登录** — `gh auth login`
3. **技能完整性检查** — SKILL.md 必须有正确的 YAML frontmatter

## 发布流程

### 第一步：登录 GitHub CLI

```bash
gh auth login
# 选择 GitHub.com → HTTPS → Login with a web browser
# 复制一次性代码 → 按回车打开浏览器 → 粘贴代码授权
```

### 第二步：创建 GitHub 仓库

**方式 A：命令行创建**
```bash
gh repo create b2b-lead-generation --public --description "通用外贸客户开发工作流"
```

**方式 B：网页创建**
1. 访问 https://github.com/new
2. Repository name: `b2b-lead-generation`
3. 选择 Public
4. 不要勾选 "Add a README file"
5. 点击 "Create repository"

### 第三步：推送代码

```bash
cd ~/.hermes/skills/b2b-lead-generation
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/你的用户名/b2b-lead-generation.git
git branch -M main
git push -u origin main
```

### 第四步：发布到 SkillHub

```bash
hermes skills publish ~/.hermes/skills/b2b-lead-generation --to github --repo 你的用户名/b2b-lead-generation
```

## ⚠️ 常见问题

### 1. "Error: --repo required"

**原因**：没有指定 GitHub repo

**解决**：必须加 `--to github --repo owner/repo`

```bash
hermes skills publish <path> --to github --repo owner/repo
```

### 2. 安全审计 "BLOCKED"

**原因**：技能中使用了 `os.environ.get()` 读取 API key，被标记为 "exfiltration"（数据外泄风险）

**这是误报！** 读取环境变量获取 API key 是标准做法。

**解决**：使用 `--force` 覆盖

```bash
hermes skills publish <path> --to github --repo owner/repo --force
```

### 3. "You are not logged into any GitHub hosts"

**原因**：GitHub CLI 未登录

**解决**：运行 `gh auth login`

### 4. 没有 GitHub 账号怎么办？

**替代方案**：

1. **打包分发**：
   ```bash
   cd ~/.hermes/skills && tar -czvf b2b-lead-generation.tar.gz b2b-lead-generation
   # 发送 tar.gz 文件给用户
   ```

2. **用户安装**：
   ```bash
   tar -xzf b2b-lead-generation.tar.gz -C ~/.hermes/skills/
   bash ~/.hermes/skills/b2b-lead-generation/scripts/install.sh
   ```

## 安全审计误报清单

本技能的安全审计结果（2026-05-13）：

| 严重度 | 类型 | 文件位置 | 实际行为 | 是否误报 |
|--------|------|---------|---------|---------|
| HIGH | exfiltration | `scripts/cli.py:39` | `os.environ.get()` | ✅ 误报 |
| HIGH | exfiltration | `scripts/core/search.py:66` | `os.environ.get()` | ✅ 误报 |
| HIGH | exfiltration | `scripts/core/enrich.py:103` | `os.environ.get()` | ✅ 误报 |
| HIGH | exfiltration | `scripts/outputs/feishu_writer.py` | `os.environ.get()` | ✅ 误报 |
| MEDIUM | execution | `scripts/cli.py:130` | `subprocess.run()` | ⚠️ 正常行为 |
| MEDIUM | persistence | `scripts/install.sh:45` | 写入 ~/.bashrc | ⚠️ 安装脚本需要 |

**结论**：所有 HIGH 级别警告都是误报（读取环境变量获取 API key），使用 `--force` 发布即可。

## 用户安装方式

发布成功后，其他人可以通过以下方式安装：

### 方式 1：SkillHub 安装（推荐）

```bash
hermes skills install b2b-lead-generation
```

### 方式 2：URL 直接安装

```bash
hermes skills install https://github.com/你的用户名/b2b-lead-generation/SKILL.md
```

### 方式 3：手动安装

```bash
git clone https://github.com/你的用户名/b2b-lead-generation.git ~/.hermes/skills/b2b-lead-generation
bash ~/.hermes/skills/b2b-lead-generation/scripts/install.sh
```
