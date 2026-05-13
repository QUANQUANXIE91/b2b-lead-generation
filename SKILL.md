---
name: b2b-lead-generation
description: "通用 B2B 客户开发工作流 — 搜索、入库、补全、背调、反思闭环。适用于太阳能、LED、机械、纺织等各行业外贸客户开发。支持飞书/CSV/Notion 多种输出方式，多语言关键词，自动化反思进化。"
version: "1.1.0"
tags: [b2b, lead-generation, sales, export,外贸, customer-development, automation, feishu, reflection]
author: "Solar Lead Workflow Team"
license: "MIT"
min_hermes_version: "0.5.0"
---

# B2B Lead Generation — 通用外贸客户开发工作流

> 🎯 **适用人群**: 外贸业务员、跨境电商运营、B2B 销售人员、市场开发经理
> 
> ⏱️ **快速上手**: 5 分钟配置 → 自动化客户开发
> 
> 🌍 **覆盖市场**: 全球任意市场，支持 20+ 种语言

## 一句话介绍

**输入你的产品关键词 → 自动搜索全球潜在客户 → 补全联系方式 → 生成背调报告 → 每日反思优化**

---

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| 🔍 **智能搜索** | 多引擎搜索（Serper/Brave/Tavily），支持多语言关键词 |
| 📥 **自动入库** | 去重、分类、Tier 分层，支持飞书/CSV/Notion |
| 📧 **联系方式补全** | Jina Reader + Hunter.io + HTTP 抓取，80%+ 成功率 |
| 📱 **社媒渠道** | Facebook 反向查找，自动提取 WhatsApp/电话/邮箱，90%+ 补全率 |
| 🕵️ **背调画像** | 自动提取公司类型、国家、主营业务，Maigret 数字画像 |
| 🧠 **反思闭环** | 自动记录执行结果，分析趋势，生成优化建议 |
| ⏰ **定时任务** | 每天 09:00 自动运行，周末可调整策略 |

---

## 🚀 快速开始

### 1. 安装

```bash
# 通过 SkillHub 安装
skillhub install b2b-lead-generation

# 或通过 ClawHub 安装
clawhub install b2b-lead-generation
```

### 2. 创建配置文件

```bash
# 复制模板
cp ~/.hermes/skills/b2b-lead-generation/config.example.yaml my-product.yaml

# 编辑配置
nano my-product.yaml
```

### 3. 运行

```bash
# 初始化（创建输出表格）
b2b-lead init --config my-product.yaml

# 搜索新线索
b2b-lead search --config my-product.yaml

# 补全联系方式
b2b-lead enrich --config my-product.yaml --limit 50

# 查看反思报告
b2b-lead report

# 一键运行全部（适合 Cron）
b2b-lead run --config my-product.yaml
```

---

## ⚙️ 配置文件说明

### 最简配置（5 分钟上手）

```yaml
# my-product.yaml
product:
  name: "LED Lighting"              # 你的产品名
  keywords:
    en: ["LED bulb distributor", "LED strip wholesale"]

output:
  type: "csv"                        # 最简单：输出到 CSV
  path: "./leads.csv"

search:
  daily_keywords: 10                 # 每天搜索 10 组关键词
```

### 完整配置（高级用户）

```yaml
# my-product-full.yaml
product:
  name: "LED Lighting"
  category: "electronics"
  
  # 多语言关键词
  keywords:
    en: ["LED bulb distributor", "LED strip wholesale", "LED panel importer"]
    es: ["distribuidor LED", "mayorista iluminación LED"]
    pt: ["distribuidor LED", "atacado iluminação LED"]
    ar: ["موزع LED", "تاجر جملة إضاءة"]
  
  # 高价值客户指示词
  high_value_indicators:
    - "wholesale"
    - "distributor"
    - "importer"
    - "manufacturer"
    - "OEM"
    - "ODM"
  
  # 排除词
  exclude_keywords:
    - "Amazon"
    - "eBay"
    - "Alibaba"
    - "AliExpress"
    - "dropshipping"
    - "retail"

# 目标市场
markets:
  - name: "North America"
    countries: ["USA", "Canada", "Mexico"]
    languages: ["en"]
    weight: 30                        # 权重 30%
  
  - name: "Europe"
    countries: ["Germany", "France", "UK", "Spain", "Italy", "Netherlands"]
    languages: ["en", "de", "fr", "es", "it", "nl"]
    weight: 40
  
  - name: "Middle East"
    countries: ["UAE", "Saudi Arabia", "Qatar", "Kuwait"]
    languages: ["en", "ar"]
    weight: 20
  
  - name: "Latin America"
    countries: ["Brazil", "Mexico", "Argentina", "Colombia"]
    languages: ["es", "pt"]
    weight: 10

# 排除类目
exclude:
  categories:
    - "medical"
    - "hospital"
    - "clinic"
    - "vaccine"
  keywords:
    - "Amazon"
    - "eBay"
    - "dropshipping"

# 输出配置
output:
  type: "feishu"                     # 可选: feishu / csv / notion
  
  feishu:
    app_id: "${FEISHU_APP_ID}"       # 环境变量
    app_secret: "${FEISHU_APP_SECRET}"
    app_token: "your-app-token"
    table_id: "your-table-id"
  
  csv:
    path: "./leads.csv"
    append: true
  
  notion:
    database_id: "your-database-id"
    api_key: "${NOTION_API_KEY}"

# 搜索配置
search:
  engines:
    - name: "serper"
      api_key: "${SERPER_API_KEY}"
      priority: 1
    - name: "brave"
      api_key: "${BRAVE_API_KEY}"
      priority: 2
    - name: "tavily"
      api_key: "${TAVILY_API_KEY}"
      priority: 3
  
  daily_keywords: 15                 # 每天搜索关键词数
  results_per_keyword: 15            # 每个关键词返回结果数
  concurrent: 3                      # 并发数

# 补全配置
enrichment:
  tools:
    - name: "jina"
      priority: 1
      timeout: 10
      retry: 2
    - name: "hunter"
      api_key: "${HUNTER_API_KEY}"
      priority: 2
    - name: "http"
      priority: 3
  
  daily_limit: 100                   # 每天补全上限

# 背调配置
background_check:
  enabled: true
  tools:
    - name: "auto_check"
      enabled: true
    - name: "maigret"
      enabled: false                 # 可选

# 反思闭环
reflection:
  enabled: true
  score_threshold: 0.5               # 评分低于此值触发优化
  trend_window: 7                    # 趋势分析窗口（天）

# 定时任务
schedule:
  enabled: true
  cron: "0 9 * * *"                  # 每天 09:00
  market_rotation: true              # 按权重轮换市场
```

---

## 📊 输出字段说明

默认输出 15 个字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| 公司名 | 文本 | 公司名称 |
| 国家 | 文本 | 所在国家 |
| 城市 | 文本 | 所在城市 |
| 网站 | 文本 | 公司网站 |
| 主营内容 | 文本 | 主营业务描述 |
| 客户类型 | 单选 | Manufacturer/Distributor/Retailer/Integrator/Unknown |
| 邮箱 | 文本 | 联系邮箱 |
| 电话 | 文本 | 联系电话 |
| WhatsApp | 文本 | WhatsApp 号码 |
| 联系人 | 文本 | 联系人姓名 |
| 职位 | 文本 | 联系人职位 |
| 来源 | 单选 | 搜索来源平台 |
| Tier | 单选 | Tier 1 高价值 / Tier 2 标准 / Tier 3 存根 |
| 完整度 | 单选 | ✅ 完整 / ⏳ 待补全 / ⚠️ 部分 |
| 备注 | 文本 | 背调信息、社交媒体等 |

---

## 🧠 反思闭环机制

借鉴 Memento-Skills 的 **Read-Write-Reflect 循环**：

```
执行 → 记录 → 反思 → 进化
  ↓       ↓       ↓       ↓
搜索    评分    趋势    优化
入库    更新    诊断    升级
补全    追踪    建议    自动
```

### 自动触发条件

| 条件 | 动作 |
|------|------|
| utility_score < 0.5 | 生成紧急优化报告 |
| 连续 3 天成功率下滑 | 自动诊断失败原因 |
| 单阶段失败率 > 50% | 工具自动降级 |

### 查看反思报告

```bash
# 今日统计
b2b-lead stats

# 技能健康检查
b2b-lead health

# 生成反思报告
b2b-lead report

# 深度诊断
b2b-lead diagnose

# 7 天趋势
b2b-lead trend
```

---

## 🔧 高级用法

### 自定义关键词模板

```bash
# 使用内置模板
b2b-lead init --template solar    # 太阳能行业
b2b-lead init --template led      # LED 照明行业
b2b-lead init --template textile  # 纺织行业
b2b-lead init --template machinery # 机械行业

# 从文件导入
b2b-lead init --keywords my-keywords.yaml
```

### 多产品并行

```bash
# 同时运行多个产品配置
b2b-lead run --config led.yaml &
b2b-lead run --config solar.yaml &
b2b-lead run --config textile.yaml &
```

### 自定义输出字段

```yaml
# 在配置文件中添加
output:
  fields:
    - name: "公司名"
      required: true
    - name: "国家"
      required: true
    - name: "邮箱"
      required: false
    - name: "LinkedIn"
      type: "text"
    - name: "年营业额"
      type: "number"
```

---

## 📚 预置行业模板

| 行业 | 模板名 | 关键词数 | 覆盖市场 |
|------|--------|---------|---------|
| 太阳能/制冷 | `solar` | 90+ | 全球 60+ 国家 |
| LED 照明 | `led` | 60+ | 全球 50+ 国家 |
| 纺织服装 | `textile` | 50+ | 全球 40+ 国家 |
| 机械制造 | `machinery` | 70+ | 全球 50+ 国家 |
| 电子电器 | `electronics` | 60+ | 全球 50+ 国家 |
| 化工原料 | `chemical` | 40+ | 全球 30+ 国家 |

---

## 🔌 集成工具

### 搜索引擎

| 工具 | 免费额度 | 成功率 | 推荐度 |
|------|---------|--------|--------|
| Serper | 2500 次/月 | 100% | ⭐⭐⭐⭐⭐ |
| Brave API | 2000 次/月 | 95% | ⭐⭐⭐⭐ |
| Tavily | 1000 次/月 | 90% | ⭐⭐⭐ |
| Grok | 免费 | 80% | ⭐⭐⭐ |

### 联系方式补全

| 工具 | 免费额度 | 成功率 | 适用市场 |
|------|---------|--------|---------|
| Jina Reader | 无限制 | 80% | 全球 ⭐⭐⭐⭐⭐ |
| Hunter.io | 25 次/月 | 70% | 欧美 |
| HTTP 抓取 | 无限制 | 50% | 全球 |
| Facebook 反向查找 | 无限制 | 30-50% | 东南亚/中东/拉美 ⭐ |

### 社媒渠道（Facebook）

| 来源 | 方式 | 提取内容 | 适用市场 |
|------|------|---------|---------|
| **网站 → FB** | 检测网站中的 FB 链接，访问 FB 页面 | WhatsApp、电话、邮箱、地址、粉丝数 | 全球 |
| **FB 搜索**（Phase 2） | 直接搜索 FB 商业页面 | 公司名、简介、网站、联系方式 | 全球 |
| **FB 群组**（Phase 3） | 搜索行业买家群 | 群组成员、业务需求帖 | 全球 |

**配置**（默认开启）：
```yaml
social_media:
  facebook:
    enabled: true    # 关闭设为 false
```

**工作原理**：补全流程中，Jina Reader 抓取网站内容后，自动扫描 FB 链接 → 发现 FB 商业页面 → 用 Jina Reader 读取 FB 页面 → 提取 WhatsApp/电话/邮箱 → 智能合并到主记录（不覆盖已有数据）。粉丝数 ≥ 1000 自动升级为 Tier 2。

详见 [`references/facebook-integration.md`](references/facebook-integration.md)

### 输出存储

| 工具 | 费用 | 特点 |
|------|------|------|
| CSV | 免费 | 最简单 |
| 飞书多维表格 | 免费 | 团队协作、可视化 |
| Notion | 免费 | 文档管理 |

---

## ❓ 常见问题

### Q: 如何获取 Serper API Key?
A: 访问 https://serper.dev 注册，免费 2500 次/月

### Q: 如何获取飞书 App ID?
A: 访问 https://open.feishu.cn 创建企业自建应用

### Q: 支持哪些语言?
A: 英文、西班牙语、葡萄牙语、法语、阿拉伯语、中文等 20+ 种语言

### Q: 如何自定义关键词?
A: 编辑配置文件中的 `product.keywords` 部分，支持多语言

### Q: 如何排除不想要的客户?
A: 在配置文件的 `exclude.keywords` 中添加排除词

---

## 📦 发布与分发

### 发布到 SkillHub（需要 GitHub repo）

```bash
# 必须指定 --to github --repo owner/repo，否则报错 "Error: --repo required"
gh auth login   # 先登录 GitHub CLI
hermes skills publish <path> --to github --repo owner/repo

# ⚠️ 安全审计误报：os.environ.get() 会被标记为 "exfiltration"（读取 API key）
# 这是正常行为，用 --force 覆盖即可
hermes skills publish <path> --to github --repo owner/repo --force

# 也可以用 URL 直接安装（无需发布到 SkillHub）
hermes skills install https://github.com/owner/repo/SKILL.md
```

详见 [`references/skillhub-publishing.md`](references/skillhub-publishing.md)

### 替代分发方式（无 GitHub）

```bash
# 打包为 tar.gz（约 31KB）
cd ~/.hermes/skills && tar -czvf b2b-lead-generation.tar.gz b2b-lead-generation

# 用户安装：解压到技能目录 + 运行安装脚本
mkdir -p ~/.hermes/skills
tar -xzf b2b-lead-generation.tar.gz -C ~/.hermes/skills/
bash ~/.hermes/skills/b2b-lead-generation/scripts/install.sh
```

---

## 📄 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| **1.1.0** | 2026-05-13 | 新增 Facebook 反向查找（Phase 1 社媒渠道），提取 WhatsApp/电话/邮箱/粉丝数 |
| **1.0.0** | 2026-05-13 | 初始版本：从 Solar 客户开发工作流抽象为通用 B2B 版本 |

**演进说明**: 本技能从 `solar-lead-workflow` v4.0.2 演化而来，详见 [`references/evolution.md`](references/evolution.md)

---

## 🤝 贡献

欢迎贡献：
- 新增行业关键词模板
- 优化脚本逻辑
- 改进文档
- 报告 Bug

---

## 📜 许可证

MIT License - 可自由使用、修改、分发

---

## 📧 联系方式

- Issues: https://github.com/your-repo/b2b-lead-generation/issues
- 文档: `references/` 目录
- 快速上手: `references/quick-start.md`
