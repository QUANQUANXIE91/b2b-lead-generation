# B2B Lead Generation 快速上手指南

> 5 分钟配置 → 自动化客户开发

## 第一步：安装

```bash
# 通过 SkillHub 安装
skillhub install b2b-lead-generation

# 或手动安装
git clone https://github.com/your-repo/b2b-lead-generation.git
cd b2b-lead-generation
```

## 第二步：创建配置文件

### 方式一：最简配置（CSV 输出）

创建 `my-product.yaml`：

```yaml
product:
  name: "LED Lighting"
  keywords:
    en:
      - "LED bulb distributor"
      - "LED strip wholesale"
      - "LED panel importer"

output:
  type: "csv"
  csv:
    path: "./leads.csv"

search:
  daily_keywords: 10
```

### 方式二：飞书输出

```yaml
product:
  name: "LED Lighting"
  keywords:
    en:
      - "LED bulb distributor"
    es:
      - "distribuidor LED"
    pt:
      - "distribuidor LED"

output:
  type: "feishu"
  feishu:
    app_id: "cli_xxxxxxxx"
    app_secret: "xxxxxxxx"
    app_token: "B3Uxxxxxxxxx"
    table_id: "tblxxxxxxxx"

search:
  engines:
    - name: "serper"
      priority: 1
  daily_keywords: 15

enrichment:
  tools:
    - name: "jina"
      priority: 1
  daily_limit: 100
```

## 第三步：配置 API Key

### 必需：搜索引擎 API Key

**Serper（推荐，免费 2500 次/月）**

1. 访问 https://serper.dev
2. 注册账号
3. 获取 API Key
4. 设置环境变量：

```bash
export SERPER_API_KEY="your-api-key"
```

### 可选：联系方式补全

**Hunter.io（免费 25 次/月）**

1. 访问 https://hunter.io
2. 注册账号
3. 获取 API Key
4. 设置环境变量：

```bash
export HUNTER_API_KEY="your-api-key"
```

**Jina Reader（推荐，免费无限）**

无需配置！直接使用。

## 第四步：运行

```bash
# 初始化配置
b2b-lead init --config my-product.yaml

# 搜索新线索
b2b-lead search --config my-product.yaml --keywords 10

# 补全联系方式
b2b-lead enrich --config my-product.yaml --limit 50

# 查看统计
b2b-lead stats --config my-product.yaml

# 一键运行全部
b2b-lead run --config my-product.yaml
```

## 第五步：设置定时任务

### 每天自动运行

```bash
# 添加到 crontab
crontab -e

# 每天 09:00 运行
0 9 * * * cd /path/to/your/project && b2b-lead run --config my-product.yaml
```

### 或使用 Hermes 定时任务

```bash
hermes cron create \
  --name "daily-lead-search" \
  --schedule "0 9 * * *" \
  --command "b2b-lead run --config my-product.yaml"
```

---

## 常见问题

### Q: 如何获取飞书多维表格的 app_token 和 table_id？

1. 打开飞书多维表格
2. 点击右上角「...」→「更多」→「获取链接」
3. 链接格式：`https://xxx.feishu.cn/base/{app_token}?table={table_id}`

### Q: 搜索结果为什么很少？

检查：
1. 关键词是否太具体？尝试更通用的词
2. API Key 是否有效？
3. 是否被限流？

### Q: 联系方式补全成功率低？

原因：
1. 网站没有公开联系方式
2. 使用了动态加载（需浏览器抓取）
3. 网站反爬虫

解决方案：
1. 使用 Hunter.io 补充
2. 手动访问网站查找
3. 使用 LinkedIn 查找联系人

---

## 下一步

- 📖 阅读 [自定义指南](customization.md)
- 🌍 查看 [多语言关键词模板](../templates/keywords.yaml)
- 🧠 了解 [反思闭环机制](../SKILL.md#反思闭环机制)

---

## 获取帮助

- GitHub Issues: https://github.com/your-repo/b2b-lead-generation/issues
- 文档: `references/` 目录
- 示例配置: `config.example.yaml`
