# B2B Lead Generation

**通用外贸客户开发工作流** — 适用于外贸业务员的客户开发自动化工具

## 一句话介绍

输入产品关键词 → 自动搜索全球潜在客户 → 补全联系方式 → 生成背调报告 → 每日反思优化

## 特性

- ✅ **多搜索引擎**: Serper/Brave/Tavily 自动降级
- ✅ **多语言支持**: 英语、西语、葡语、阿拉伯语等 20+ 种语言
- ✅ **多输出方式**: CSV（最简单）、飞书多维表格（团队协作）、Notion
- ✅ **联系方式补全**: Jina Reader（免费无限）+ Hunter.io + HTTP 抓取
- ✅ **反思闭环**: 自动记录效果、分析趋势、优化策略
- ✅ **预置模板**: 8 大行业 × 10 大市场，450+ 关键词

## 快速开始

```bash
# 安装
skillhub install b2b-lead-generation

# 创建配置
cp ~/.hermes/skills/b2b-lead-generation/config.example.yaml my-product.yaml

# 编辑配置（填入你的产品关键词）
nano my-product.yaml

# 运行搜索
b2b-lead search --config my-product.yaml

# 补全联系方式
b2b-lead enrich --config my-product.yaml
```

## 预置行业

| 行业 | 模板名 | 关键词数 |
|------|--------|---------|
| 太阳能/制冷 | `solar` | 90+ |
| LED 照明 | `led` | 60+ |
| 纺织服装 | `textile` | 50+ |
| 机械制造 | `machinery` | 70+ |
| 电子电器 | `electronics` | 60+ |
| 化工原料 | `chemical` | 40+ |
| 汽车配件 | `auto_parts` | 40+ |
| 五金工具 | `hardware` | 40+ |

## 预置市场

东南亚、中东、拉美、非洲、南亚、欧洲、北美、大洋洲、中亚、东亚

## 文档

- [快速上手](references/quick-start.md)
- [配置说明](config.example.yaml)
- [关键词模板](templates/keywords.yaml)
- [市场模板](templates/markets.yaml)

## 许可证

MIT License

## 作者

Solar Lead Workflow Team
