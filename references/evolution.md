# B2B Lead Generation 技能演进说明

## 版本来源

`b2b-lead-generation` v1.0.0 从 `solar-lead-workflow` v4.0.2 演化而来。

**演化日期**: 2026-05-13

## 为什么演化

`solar-lead-workflow` 专为 Solar 制冷产品设计，关键词、市场配置都硬编码在脚本中。用户希望创建一个通用版本，让 80-90% 的外贸业务员都能使用，支持任意产品类型。

## 关键变更

| 维度 | solar-lead-workflow v4.0.2 | b2b-lead-generation v1.0.0 |
|------|---------------------------|---------------------------|
| 产品类型 | 硬编码 Solar | YAML 配置任意产品 |
| 关键词 | 写死在代码里 | `product.keywords` 配置 |
| 市场 | 五大市场固定 | 用户自定义 `markets` 列表 |
| 存储 | 仅飞书 | 飞书/CSV/Notion 可选 |
| 排除词 | 医疗类硬编码 | `exclude` 配置自定义 |
| CLI | `python scripts/xxx` | `b2b-lead xxx` 统一命令 |
| 预置模板 | 无 | 8 行业 × 10 市场 |

## 保留的核心机制

1. **反思闭环** — 三层架构（reflection_logger + daily_reflection + skill_meta.json）
2. **多引擎搜索** — Serper/Brave/Tavily 优先级降级
3. **联系方式补全** — Jina Reader + Hunter.io + HTTP 三级降级
4. **客户类型识别** — DOMAIN_TYPE_MAP 域名关键词匹配
5. **电话区号验证** — PHONE_AREA_CODES 国家映射

## 迁移指南

### 从 solar-lead-workflow 迁移

```bash
# 1. 复制关键词到配置文件
cp ~/.hermes/skills/b2b-lead-generation/templates/keywords.yaml my-solar.yaml

# 2. 选择 solar 行业关键词
# 编辑 my-solar.yaml，只保留 product.keywords.solar 部分

# 3. 配置市场（参考 templates/markets.yaml）

# 4. 配置飞书输出
# output.type: feishu
# output.feishu.app_token/table_id 使用原 Solar 表格

# 5. 运行
b2b-lead search --config my-solar.yaml
```

### 配置对应关系

| solar-lead-workflow | b2b-lead-generation |
|---------------------|---------------------|
| `KEYWORDS_BY_LANG` | `product.keywords` |
| `TARGET_MARKETS` | `markets` |
| `EXCLUDE_CATEGORIES` | `exclude.categories` |
| `FEISHU_APP_TOKEN` | `output.feishu.app_token` |
| `SERPER_API_KEY` | 环境变量（相同） |

## 维护策略

1. **bug 修复** — 两个技能共享相同的核心逻辑，修复一处应同步到另一处
2. **功能增强** — 优先在 `b2b-lead-generation` 实现，`solar-lead-workflow` 可选择性合并
3. **模板扩展** — 新增行业关键词模板放入 `templates/keywords.yaml`

## 文件对照表

| solar-lead-workflow | b2b-lead-generation |
|---------------------|---------------------|
| `scripts/contact_scraper.py` | `scripts/core/enrich.py` (重构) |
| `scripts/auto_background_check.py` | 内置到 enrich.py |
| `scripts/lark_client.py` | `scripts/outputs/feishu_writer.py` |
| `scripts/reflection_logger.py` | `skill_meta.json` (简化) |
| `scripts/daily_reflection.py` | 内置到 CLI `report` 命令 |
| `references/multilingual-keywords.md` | `templates/keywords.yaml` |
