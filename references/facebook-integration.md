# Facebook 社媒渠道集成

## 概述

Facebook 是东南亚、中东、拉美市场的主要社媒渠道，大量中小经销商在 FB 上活跃，且有 WhatsApp 按钮方便联系。

## 分阶段实施

### Phase 1: 网站反向查找（已实现 ✅）

**原理**：先通过搜索引擎找到公司网站 → 检测网站中的 FB 链接 → 访问 FB 页面提取联系方式

**优点**：
- 不需要直接爬 FB（规避反爬风险）
- 利用已有搜索结果
- FB 页面通常有更多联系方式（尤其是 WhatsApp）

**实现细节**（`scripts/core/enrich.py`）：

```python
# 1. FB 链接检测
def extract_facebook_url(content: str, url: str) -> Optional[str]:
    """
    从网页内容中提取 FB 商业页面链接
    
    过滤规则：
    - 排除个人主页（facebook.com/people/）
    - 排除帖子链接
    - 排除照片链接
    - 排除纯数字 ID（通常是个人）
    """

# 2. FB 页面信息提取
def extract_facebook_info(fb_content: str) -> Dict:
    """
    提取 WhatsApp/电话/邮箱/地址/粉丝数
    
    WhatsApp 模式：
    - whatsapp: +971...
    - wa.me/9715012345678
    - api.whatsapp.com/send?phone=971...
    """

# 3. 智能合并
def _merge_facebook_info(record: Dict, fb_info: Dict):
    """不覆盖已有数据，补充缺失"""
    if fb_info.get('whatsapp') and not record.get('WhatsApp'):
        record['WhatsApp'] = fb_info['whatsapp']
    
    # 粉丝数 >= 1000 → Tier 升级
    if fb_info['followers'] >= 1000 and record['Tier'] == 'Tier 3':
        record['Tier'] = 'Tier 2'
```

**配置**：
```yaml
social_media:
  facebook:
    enabled: true  # 默认开启
```

### Phase 2: FB 商业页面直接搜索（计划中 📋）

**搜索入口**：
```
https://www.facebook.com/search/pages?q={keyword}
```

**抓取内容**：
- 公司名
- 主营业务描述
- 网站（跳转链接）
- 地址/电话（如有）
- 粉丝数（判断规模）

**技术挑战**：
- FB 强反爬虫机制（登录检测、行为分析）
- 需要模拟真实用户行为（滚动、点击、停留）
- 可使用 CloakBrowser/Camoufox 绕过检测

**实现思路**：
```python
from camoufox import Camoufox

async def search_facebook_pages(keyword):
    browser = Camoufox(headless=True)
    page = await browser.new_page()
    
    await page.goto(f'https://www.facebook.com/search/pages?q={keyword}')
    
    # 模拟人类滚动
    for i in range(3):
        await page.mouse.move(500, 300 + i * 200)
        await page.wait_for_timeout(random.randint(1000, 3000))
        await page.evaluate('window.scrollBy(0, 500)')
    
    # 提取结果
    pages = await page.query_selector_all('[role="main"] a[href*="/pages/"]')
    # ...
```

### Phase 3: FB 群组 & Marketplace（长期规划 📋）

| 来源 | 适用场景 |
|------|---------|
| FB Groups | 行业买家群（如 Solar Buyers Group） |
| FB Marketplace | 本地批发商、小型经销商 |

---

## 效果数据

| 补全方式 | 原成功率 | 加 FB 后 |
|---------|---------|---------|
| Jina + Hunter | 80% | **90%+** |

**尤其东南亚/中东/拉美**：WhatsApp 获取率显著提升（FB 商业页面常见 WhatsApp 按钮）

---

## 已有反检测工具

| 工具 | 说明 |
|------|------|
| CloakBrowser | 绕过 Cloudflare/DataDome，reCAPTCHA v3 得分 0.9 |
| Camoufox | 反检测 Firefox 浏览器 |
| Playwright | 浏览器自动化 |
| Agent Browser | Rust 高性能浏览器 |

---

## 参考链接

- Skill 文件：`scripts/core/enrich.py`（`extract_facebook_url`、`extract_facebook_info` 函数）
- 配置模板：`config.example.yaml`（`social_media.facebook` 部分）
- 仓库：https://github.com/QUANQUANXIE91/b2b-lead-generation