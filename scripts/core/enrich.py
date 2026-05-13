#!/usr/bin/env python3
"""
B2B Lead Generation - Contact Enrichment Module
联系方式补全模块

功能：
- Jina Reader 网页抓取（零配置，推荐）
- Hunter.io 邮箱查找
- HTTP 直接抓取（兜底）
- 邮箱/电话/WhatsApp/联系人提取
- 客户类型重识别
- 电话区号验证

用法：
    python enrich.py --config my-product.yaml --input leads.json --limit 50
"""

import os
import re
import json
import yaml
import time
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import requests

# ============================================================
# 客户类型域名匹配（按优先级排序）
# ============================================================

DOMAIN_TYPE_MAP = [
    ("wholesale", "Distributor"),
    ("distribut", "Distributor"),
    ("trading", "Trading Company"),
    ("coldroom", "Integrator"),
    ("refrigeration", "Integrator"),
    ("freezer", "Integrator"),
    ("cooling", "Integrator"),
    ("solar", "Manufacturer"),
    ("energy", "Manufacturer"),
    ("power", "Manufacturer"),
]

# 无效电话号码（精确匹配集合）
PHONE_INVALID_EXACT = {'00000000', '12345678', '11111111', '99999999', '31536000'}

# 电话区号映射（常用国家）
PHONE_AREA_CODES = {
    # 东南亚
    "+60": "Malaysia", "+65": "Singapore", "+66": "Thailand",
    "+62": "Indonesia", "+63": "Philippines", "+84": "Vietnam",
    "+855": "Cambodia", "+95": "Myanmar", "+673": "Brunei",
    "+674": "Nauru", "+680": "Palau", "+691": "Micronesia",
    "+692": "Marshall Islands",
    # 中东
    "+971": "UAE", "+966": "Saudi Arabia", "+974": "Qatar",
    "+965": "Kuwait", "+968": "Oman", "+973": "Bahrain",
    "+964": "Iraq", "+962": "Jordan", "+961": "Lebanon",
    "+20": "Egypt", "+212": "Morocco", "+216": "Tunisia",
    "+213": "Algeria",
    # 拉美
    "+55": "Brazil", "+52": "Mexico", "+54": "Argentina",
    "+57": "Colombia", "+56": "Chile", "+51": "Peru",
    "+593": "Ecuador", "+58": "Venezuela", "+598": "Uruguay",
    "+595": "Paraguay", "+591": "Bolivia", "+503": "El Salvador",
    "+504": "Honduras", "+502": "Guatemala", "+506": "Costa Rica",
    "+507": "Panama", "+53": "Cuba", "+809": "Dominican Republic",
    # 非洲
    "+254": "Kenya", "+234": "Nigeria", "+27": "South Africa",
    "+233": "Ghana", "+237": "Cameroon", "+251": "Ethiopia",
    "+249": "Sudan", "+212": "Morocco", "+20": "Egypt",
    "+231": "Liberia", "+232": "Sierra Leone", "+228": "Togo",
    "+229": "Benin", "+225": "Ivory Coast", "+226": "Burkina Faso",
    "+223": "Mali", "+221": "Senegal", "+220": "Gambia",
    # 南亚
    "+91": "India", "+92": "Pakistan", "+880": "Bangladesh",
    "+94": "Sri Lanka", "+977": "Nepal", "+975": "Bhutan",
    # 欧洲
    "+49": "Germany", "+33": "France", "+44": "UK", "+34": "Spain",
    "+39": "Italy", "+31": "Netherlands", "+41": "Switzerland",
    "+43": "Austria", "+32": "Belgium", "+351": "Portugal",
    "+48": "Poland", "+46": "Sweden", "+47": "Norway",
    "+45": "Denmark", "+358": "Finland", "+30": "Greece",
    # 大洋洲
    "+61": "Australia", "+64": "New Zealand",
    # 北美
    "+1": "USA/Canada",
}


# ============================================================
# 工具函数
# ============================================================

def load_config(config_path: str) -> Dict:
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    def expand_env(obj):
        if isinstance(obj, str) and obj.startswith('${') and obj.endswith('}'):
            return os.environ.get(obj[2:-1], obj)
        elif isinstance(obj, dict):
            return {k: expand_env(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [expand_env(item) for item in obj]
        return obj
    
    return expand_env(config)


def extract_emails(text: str) -> List[str]:
    """从文本中提取邮箱"""
    if not text:
        return []
    
    # 标准邮箱正则
    pattern = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
    emails = re.findall(pattern, text)
    
    # 过滤无效邮箱
    valid = []
    invalid_domains = ['example.com', 'email.com', 'test.com', 'domain.com',
                       'company.com', 'yourdomain.com', 'yoursite.com']
    
    for email in emails:
        email_lower = email.lower()
        domain = email_lower.split('@')[1] if '@' in email_lower else ''
        
        if domain in invalid_domains:
            continue
        if any(x in email_lower for x in ['png', 'jpg', 'gif', 'svg', 'webp']):
            continue
        if '..' in email_lower:
            continue
        
        valid.append(email_lower)
    
    return list(set(valid))


def extract_phones(text: str) -> List[str]:
    """从文本中提取电话号码"""
    if not text:
        return []
    
    phones = []
    
    # 国际格式 +XXX
    intl_pattern = r'\+\d{1,4}[\s\-\.]?\d{4,14}'
    for match in re.findall(intl_pattern, text):
        digits = re.sub(r'[^\d+]', '', match)
        if len(digits) >= 8 and len(digits) <= 16:
            phones.append(digits)
    
    # 括号格式 (XXX) XXX-XXXX
    local_pattern = r'\(?\d{2,4}\)?[\s\-\.]?\d{3,4}[\s\-\.]?\d{4}'
    for match in re.findall(local_pattern, text):
        digits = re.sub(r'[^\d]', '', match)
        if len(digits) >= 8 and len(digits) <= 15:
            phones.append(digits)
    
    # WhatsApp 格式
    wa_pattern = r'whatsapp[:\s]*(\+?\d[\d\s\-]{7,15})'
    for match in re.findall(wa_pattern, text, re.IGNORECASE):
        digits = re.sub(r'[^\d+]', '', match)
        if len(digits) >= 8:
            phones.append(digits)
    
    # 过滤无效号码（精确匹配）
    valid = []
    seen_digits = set()
    
    for phone in phones:
        digits_only = re.sub(r'[^\d]', '', phone)
        if digits_only in PHONE_INVALID_EXACT:
            continue
        if digits_only in seen_digits:
            continue
        seen_digits.add(digits_only)
        valid.append(phone.strip())
    
    return valid


def detect_phone_country(phone: str) -> Optional[str]:
    """根据电话区号检测国家"""
    for code, country in sorted(PHONE_AREA_CODES.items(), key=lambda x: -len(x[0])):
        if phone.startswith(code):
            return country
    return None


def extract_whatsapp(text: str, phones: List[str]) -> Optional[str]:
    """提取 WhatsApp 号码"""
    # 先检查明确的 WhatsApp 提及
    wa_pattern = r'whatsapp[:\s]*([\+\d\s\-]{8,20})'
    matches = re.findall(wa_pattern, text, re.IGNORECASE)
    if matches:
        return re.sub(r'[^\d+]', '', matches[0])
    
    # 检查手机号（非座机）
    mobile_indicators = ['mobile', 'cell', 'hp', 'handphone', 'celular']
    text_lower = text.lower()
    
    if any(ind in text_lower for ind in mobile_indicators) and phones:
        return phones[0]
    
    return None


def detect_customer_type_from_text(title: str, description: str, url: str, content: str = "") -> str:
    """从网站内容检测客户类型"""
    text = f"{title} {description} {url} {content}".lower()
    
    # 优先级匹配
    for keyword, customer_type in DOMAIN_TYPE_MAP:
        if keyword in text:
            return customer_type
    
    # 额外关键词
    extra_patterns = [
        (r'\bbuyer\b', "Buyer"),
        (r'\bretailer\b', "Retailer"),
        (r'\bcontractor\b', "Integrator"),
        (r'\binstaller\b', "Integrator"),
        (r'\bagent\b', "Trading Company"),
        (r'\bbroker\b', "Trading Company"),
        (r'\bdistributor\b', "Distributor"),
        (r'\bmanufacturer\b', "Manufacturer"),
        (r'\bOEM\b', "Manufacturer"),
        (r'\bODM\b', "Manufacturer"),
    ]
    
    for pattern, customer_type in extra_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return customer_type
    
    return "Unknown"


def clean_content(text: str) -> str:
    """清洗网页内容"""
    if not text:
        return ""
    
    # 移除 HTML 标签
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # 移除多余空白
    text = re.sub(r'\s+', ' ', text)
    
    # 移除 CSS/JS 代码块
    text = re.sub(r'\{[^}]*\}', ' ', text)
    
    return text.strip()


def extract_facebook_url(content: str, url: str) -> Optional[str]:
    """
    从网页内容中提取 Facebook 链接
    
    优先级：
    1. 官方主页链接（facebook.com/公司名）
    2. 任何 FB 链接
    
    排除：
    - 个人主页（facebook.com/people/）
    - 帖子链接（posts/）
    - 照片链接（photos/）
    """
    if not content:
        return None
    
    # 常见 FB 链接模式
    patterns = [
        r'facebook\.com/([a-zA-Z0-9.\-]+)',
        r'fb\.com/([a-zA-Z0-9.\-]+)',
        r'm\.facebook\.com/([a-zA-Z0-9.\-]+)',
    ]
    
    all_matches = []
    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        all_matches.extend(matches)
    
    # 过滤掉非商业页面
    excluded_keywords = [
        'people', 'posts', 'photos', 'videos', 'groups', 'events',
        'marketplace', 'stories', 'reel', 'watch', 'gaming',
        'share', 'sharer', 'plugins', 'dialog', 'login', 'signup'
    ]
    
    business_urls = []
    for username in set(all_matches):
        username_lower = username.lower()
        
        # 排除个人页面和帖子
        if any(kw in username_lower for kw in excluded_keywords):
            continue
        
        # 排除纯数字ID（通常是个人）
        if username.isdigit():
            continue
        
        # 构建完整 URL
        clean_username = username.split('?')[0]  # 移除查询参数
        fb_url = f"https://www.facebook.com/{clean_username}"
        business_urls.append(fb_url)
    
    if business_urls:
        # 优先返回第一个（通常是最重要的）
        return business_urls[0]
    
    return None


def extract_facebook_info(fb_content: str) -> Dict:
    """
    从 Facebook 页面内容中提取信息
    
    提取内容：
    - WhatsApp 号码（商业页面常见）
    - 电话
    - 邮箱
    - 地址
    - 公司简介
    - 粉丝数（规模判断）
    """
    if not fb_content:
        return {}
    
    info = {}
    
    # WhatsApp（FB 商业页面常见）
    wa_patterns = [
        r'whatsapp[:\s]*([+\d][\d\s\-]{7,20})',
        r'wa\.me/(\d+)',
        r'api\.whatsapp\.com/send\?phone=(\d+)',
    ]
    
    for pattern in wa_patterns:
        match = re.search(pattern, fb_content, re.IGNORECASE)
        if match:
            phone = re.sub(r'[^\d+]', '', match.group(1))
            if len(phone) >= 8:
                info['whatsapp'] = phone
                break
    
    # 电话
    phone_patterns = [
        r'\+?\d{1,4}[\s\-\.]?\(?\d{2,4}\)?[\s\-\.]?\d{3,4}[\s\-\.]?\d{3,4}',
        r'Tel[:\s]*([+\d][\d\s\-]{7,15})',
        r'Phone[:\s]*([+\d][\d\s\-]{7,15})',
        r'Call[:\s]*([+\d][\d\s\-]{7,15})',
    ]
    
    phones = []
    for pattern in phone_patterns:
        matches = re.findall(pattern, fb_content, re.IGNORECASE)
        for m in matches:
            phone = re.sub(r'[^\d+]', '', m if isinstance(m, str) else m[0])
            if len(phone) >= 8 and phone not in PHONE_INVALID_EXACT:
                phones.append(phone)
    
    if phones:
        info['phone'] = phones[0]
    
    # 邮箱
    emails = extract_emails(fb_content)
    if emails:
        info['email'] = emails[0]
    
    # 地址（可能包含城市/国家信息）
    address_patterns = [
        r'Address[:\s]*([^\n]{10,100})',
        r'Location[:\s]*([^\n]{5,50})',
        r'Address\n([^\n]{10,100})',
    ]
    
    for pattern in address_patterns:
        match = re.search(pattern, fb_content, re.IGNORECASE)
        if match:
            address = match.group(1).strip()
            # 清洗地址
            address = re.sub(r'\s+', ' ', address)
            if len(address) > 5:
                info['address'] = address
                break
    
    # 粉丝数（判断规模）
    follower_patterns = [
        r'(\d+[\d,]*)\s*(?:followers?|likes|people)',
        r'(\d+[\d,]*)\s*(?:人关注|关注|赞)',
    ]
    
    for pattern in follower_patterns:
        match = re.search(pattern, fb_content, re.IGNORECASE)
        if match:
            followers = match.group(1).replace(',', '')
            try:
                info['followers'] = int(followers)
            except:
                pass
            break
    
    return info


# ============================================================
# 补全工具
# ============================================================

class JinaReader:
    """Jina Reader — 零配置网页转 Markdown"""
    
    def __init__(self, timeout: int = 10, retry: int = 2):
        self.timeout = timeout
        self.retry = retry
        self.base_url = "https://r.jina.ai/"
    
    def read(self, url: str) -> Optional[str]:
        """读取网页内容"""
        for attempt in range(self.retry + 1):
            try:
                resp = requests.get(
                    f"{self.base_url}{url}",
                    headers={"Accept": "text/plain"},
                    timeout=self.timeout
                )
                if resp.status_code == 200:
                    return resp.text
                elif resp.status_code == 429:
                    wait = (attempt + 1) * 5
                    print(f"  [JINA] Rate limited, waiting {wait}s...")
                    time.sleep(wait)
                    continue
                else:
                    print(f"  [JINA] HTTP {resp.status_code}")
                    return None
            except requests.Timeout:
                print(f"  [JINA] Timeout (attempt {attempt + 1}/{self.retry + 1})")
                if attempt < self.retry:
                    time.sleep(3)
                continue
            except Exception as e:
                print(f"  [JINA] Error: {e}")
                return None
        
        return None


class HunterIO:
    """Hunter.io 邮箱查找"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("HUNTER_API_KEY")
    
    def find_emails(self, domain: str) -> List[str]:
        """查找域名关联邮箱"""
        if not self.api_key:
            return []
        
        try:
            resp = requests.get(
                "https://api.hunter.io/v2/domain-search",
                params={"domain": domain, "api_key": self.api_key},
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                emails = []
                for item in data.get("data", {}).get("emails", []):
                    emails.append(item.get("value", ""))
                return emails
        except Exception as e:
            print(f"  [HUNTER] Error: {e}")
        
        return []


class HTTPScraper:
    """HTTP 直接抓取"""
    
    def __init__(self, timeout: int = 15):
        self.timeout = timeout
    
    def scrape(self, url: str) -> Optional[str]:
        """抓取网页"""
        try:
            resp = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; B2B-Bot/1.0)"},
                timeout=self.timeout
            )
            if resp.status_code == 200:
                return resp.text[:50000]  # 限制大小
        except Exception as e:
            print(f"  [HTTP] Error: {e}")
        
        return None


# ============================================================
# 补全流程
# ============================================================

class ContactEnricher:
    """联系方式补全器"""
    
    def __init__(self, config: Dict):
        self.config = config
        
        # 初始化工具
        enrichment_config = config.get("enrichment", {}).get("tools", [])
        self.tools = {}
        
        for tool_config in enrichment_config:
            name = tool_config.get("name")
            if name == "jina":
                self.tools["jina"] = JinaReader(
                    timeout=tool_config.get("timeout", 10),
                    retry=tool_config.get("retry", 2)
                )
            elif name == "hunter":
                self.tools["hunter"] = HunterIO(tool_config.get("api_key"))
            elif name == "http":
                self.tools["http"] = HTTPScraper(tool_config.get("timeout", 15))
        
        # 如果没配置，使用默认
        if "jina" not in self.tools:
            self.tools["jina"] = JinaReader()
        if "http" not in self.tools:
            self.tools["http"] = HTTPScraper()
    
    def enrich_record(self, record: Dict) -> Dict:
        """补全单条记录"""
        url = record.get("网站", "")
        domain = record.get("域名", "") or ""
        
        if not domain and url:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc.lower()
            record["域名"] = domain
        
        if not domain:
            record["完整度"] = "⚠️ 部分"
            return record
        
        # 1. Jina Reader 抓取
        content = None
        if "jina" in self.tools:
            content = self.tools["jina"].read(url)
            if content:
                content = clean_content(content)
                print(f"  [JINA] OK ({len(content)} chars)")
        
        # 2. Hunter.io 查邮箱
        emails_from_hunter = []
        if "hunter" in self.tools and not record.get("email"):
            emails_from_hunter = self.tools["hunter"].find_emails(domain)
            if emails_from_hunter:
                print(f"  [HUNTER] Found {len(emails_from_hunter)} emails")
        
        # 3. HTTP 兜底
        if not content and "http" in self.tools:
            content = self.tools["http"].scrape(url)
            if content:
                content = clean_content(content)
                print(f"  [HTTP] OK ({len(content)} chars)")
        
        # 提取信息
        combined_text = f"{content or ''} {record.get('主营内容', '')}"
        
        # 邮箱
        emails = extract_emails(combined_text)
        emails.extend(emails_from_hunter)
        if emails:
            # 优先选择 info/sales 前缀
            priority_prefixes = ['sales', 'info', 'contact', 'export', 'trade']
            priority_emails = [e for e in emails if e.split('@')[0] in priority_prefixes]
            record["email"] = priority_emails[0] if priority_emails else emails[0]
        
        # 电话
        phones = extract_phones(combined_text)
        if phones:
            record["phone"] = phones[0]
            # 检测国家
            phone_country = detect_phone_country(phones[0])
            if phone_country and not record.get("国家"):
                record["country_detected"] = phone_country
        
        # WhatsApp
        whatsapp = extract_whatsapp(combined_text, phones)
        if whatsapp:
            record["WhatsApp"] = whatsapp
        
        # 客户类型重识别
        if content:
            record["客户类型"] = detect_customer_type_from_text(
                record.get("公司名", ""),
                record.get("主营内容", ""),
                url,
                content
            )
        
        # ============================================================
        # 4. Facebook 反向查找（Phase 1 社媒渠道）
        # ============================================================
        social_enabled = self.config.get("social_media", {}).get("facebook", {}).get("enabled", True)
        if social_enabled and content:
            fb_url = extract_facebook_url(content, url)
            if fb_url:
                print(f"  [FB] Found page: {fb_url}")
                record["Facebook"] = fb_url
                
                # 用 Jina Reader 读取 FB 页面
                fb_info = self._enrich_from_facebook(fb_url)
                if fb_info:
                    # 合并 FB 信息（不覆盖已有数据）
                    self._merge_facebook_info(record, fb_info)
        
        # 更新完整度
        record["完整度"] = self._calc_completeness(record)
        
        # 更新 Tier
        record["Tier"] = self._calc_tier(record)
        
        return record
    
    def _enrich_from_facebook(self, fb_url: str) -> Optional[Dict]:
        """通过 Jina Reader 读取 Facebook 页面提取信息"""
        if "jina" not in self.tools:
            return None
        
        try:
            # FB 页面用更长的超时
            jina = self.tools["jina"]
            old_timeout = jina.timeout
            jina.timeout = 15  # FB 页面需要更长超时
            
            fb_content = jina.read(fb_url)
            jina.timeout = old_timeout  # 恢复
            
            if not fb_content:
                print(f"  [FB] Failed to read page")
                return None
            
            fb_content = clean_content(fb_content)
            if not fb_content or len(fb_content) < 50:
                print(f"  [FB] Page too short ({len(fb_content) if fb_content else 0} chars)")
                return None
            
            info = extract_facebook_info(fb_content)
            if info:
                found = []
                if info.get('whatsapp'):
                    found.append(f"WA:{info['whatsapp']}")
                if info.get('phone'):
                    found.append(f"Tel:{info['phone']}")
                if info.get('email'):
                    found.append(f"Email:{info['email']}")
                if info.get('followers'):
                    found.append(f"{info['followers']}followers")
                print(f"  [FB] Extracted: {', '.join(found)}")
            
            return info if info else None
            
        except Exception as e:
            print(f"  [FB] Error: {e}")
            return None
    
    def _merge_facebook_info(self, record: Dict, fb_info: Dict):
        """合并 Facebook 提取的信息到主记录（不覆盖已有数据）"""
        # WhatsApp（优先使用 FB 的，通常更准确）
        if fb_info.get('whatsapp') and not record.get('WhatsApp'):
            record['WhatsApp'] = fb_info['whatsapp']
        
        # 电话
        if fb_info.get('phone') and not record.get('phone'):
            record['phone'] = fb_info['phone']
            phone_country = detect_phone_country(fb_info['phone'])
            if phone_country and not record.get('国家'):
                record['country_detected'] = phone_country
        
        # 邮箱
        if fb_info.get('email') and not record.get('email'):
            record['email'] = fb_info['email']
        
        # 地址 → 备注
        if fb_info.get('address'):
            existing_notes = record.get('备注', '')
            if 'FB地址' not in existing_notes:
                record['备注'] = f"{existing_notes} | FB地址: {fb_info['address']}".strip(' |')
        
        # 粉丝数 → 备注
        if fb_info.get('followers'):
            existing_notes = record.get('备注', '')
            if 'FB粉丝' not in existing_notes:
                record['备注'] = f"{existing_notes} | FB粉丝: {fb_info['followers']}".strip(' |')
            
            # 粉丝数影响 Tier
            if fb_info['followers'] >= 1000 and record['Tier'] == 'Tier 3':
                record['Tier'] = 'Tier 2'  # 有规模的升级
    
    def _calc_completeness(self, record: Dict) -> str:
        has_email = bool(record.get("email"))
        has_phone = bool(record.get("phone"))
        has_contact = bool(record.get("联系人"))
        
        if has_email and has_phone:
            return "✅ 完整"
        elif has_email or has_phone:
            return "⏳ 待补全"
        else:
            return "⚠️ 部分"
    
    def _calc_tier(self, record: Dict) -> str:
        has_email = bool(record.get("email"))
        has_phone = bool(record.get("phone"))
        ctype = record.get("客户类型", "Unknown")
        
        if ctype in ["Distributor", "Integrator"] and (has_email or has_phone):
            return "Tier 1"
        elif ctype != "Unknown" and (has_email or has_phone):
            return "Tier 2"
        else:
            return "Tier 3"
    
    def run(self, records: List[Dict], limit: Optional[int] = None) -> List[Dict]:
        """
        批量补全
        
        Args:
            records: 待补全的记录列表
            limit: 最大补全数量（None 则全部）
        """
        if limit:
            records = records[:limit]
        
        print(f"\n{'='*60}")
        print(f"Contact Enrichment - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        print(f"Records to enrich: {len(records)}")
        print(f"Tools: {list(self.tools.keys())}")
        print(f"{'='*60}\n")
        
        enriched = []
        success = 0
        failed = 0
        
        for i, record in enumerate(records, 1):
            url = record.get("网站", "")
            print(f"[{i}/{len(records)}] {url[:60]}")
            
            try:
                record = self.enrich_record(record)
                enriched.append(record)
                
                if record.get("email") or record.get("phone"):
                    success += 1
                    print(f"  ✓ email={record.get('email', 'N/A')} phone={record.get('phone', 'N/A')}")
                else:
                    failed += 1
                    print(f"  ✗ No contact found")
            except Exception as e:
                failed += 1
                print(f"  ✗ Error: {e}")
                enriched.append(record)
            
            # 礼貌延迟
            if i < len(records):
                time.sleep(random.uniform(1, 3))
        
        # 汇总
        print(f"\n{'='*60}")
        print(f"Enrichment Complete!")
        print(f"{'='*60}")
        print(f"Total: {len(enriched)}")
        print(f"Success: {success} ({success/len(enriched)*100:.1f}%)")
        print(f"Failed: {failed} ({failed/len(enriched)*100:.1f}%)")
        
        # 按完整度统计
        completeness = {}
        for r in enriched:
            c = r.get("完整度", "⚠️ 部分")
            completeness[c] = completeness.get(c, 0) + 1
        print(f"Completeness:")
        for c, count in sorted(completeness.items()):
            print(f"  {c}: {count}")
        print(f"{'='*60}\n")
        
        return enriched


# ============================================================
# CLI 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="B2B Lead Enrichment")
    parser.add_argument("--config", required=True, help="Config file path")
    parser.add_argument("--input", required=True, help="Input JSON file with records")
    parser.add_argument("--output", help="Output JSON file path")
    parser.add_argument("--limit", type=int, default=50, help="Max records to enrich")
    parser.add_argument("--filter", choices=["incomplete", "all"], default="incomplete",
                       help="Filter records: incomplete (default) or all")
    
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config)
    
    # 加载记录
    with open(args.input, 'r', encoding='utf-8') as f:
        records = json.load(f)
    
    # 过滤
    if args.filter == "incomplete":
        records = [r for r in records if r.get("完整度", "") != "✅ 完整"]
        print(f"Filtered to {len(records)} incomplete records")
    
    # 补全
    enricher = ContactEnricher(config)
    enriched = enricher.run(records, args.limit)
    
    # 输出
    output = args.output or args.input
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(enriched)} records to {output}")


if __name__ == "__main__":
    main()
