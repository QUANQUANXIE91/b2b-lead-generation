#!/usr/bin/env python3
"""
B2B Lead Generation - Core Search Module
通用 B2B 客户搜索模块

功能：
- 多搜索引擎支持（Serper/Brave/Tavily）
- 多语言关键词组合
- 智能去重和过滤
- 客户类型识别
- Tier 分层

用法：
    python search.py --config my-product.yaml --keywords 10
"""

import os
import sys
import json
import yaml
import random
import hashlib
import argparse
from datetime import datetime
from urllib.parse import urlparse
from typing import Dict, List, Optional, Tuple
import requests

# ============================================================
# 配置常量
# ============================================================

# 客户类型域名匹配（按优先级排序）
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

# 无效电话号码（精确匹配）
PHONE_INVALID_EXACT = {'00000000', '12345678', '11111111', '99999999', '31536000'}

# 数据清洗黑名单
BLACKLIST_PATTERNS = [
    r'@2x\.', r'@3x\.',  # 图片倍率
    r'slick-carousel', r'aos\.', r'sweetalert',  # JS 库
    r'npm\.', r'github\.com/',  # NPM/GitHub
    r'gravatar\.com', r'schema\.org', r'w3\.org',  # 元数据
]

# ============================================================
# 搜索引擎封装
# ============================================================

class SearchEngine:
    """搜索引擎基类"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get(self.env_var)
    
    @property
    def name(self) -> str:
        raise NotImplementedError
    
    @property
    def env_var(self) -> str:
        raise NotImplementedError
    
    def search(self, query: str, num_results: int = 15) -> List[Dict]:
        raise NotImplementedError


class SerperEngine(SearchEngine):
    """Serper 搜索引擎（推荐）"""
    
    name = "serper"
    env_var = "SERPER_API_KEY"
    
    def search(self, query: str, num_results: int = 15) -> List[Dict]:
        if not self.api_key:
            print(f"[WARNING] {self.name}: API key not configured")
            return []
        
        try:
            resp = requests.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": self.api_key},
                json={"q": query, "num": num_results},
                timeout=30
            )
            resp.raise_for_status()
            data = resp.json()
            
            results = []
            for item in data.get("organic", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "description": item.get("snippet", ""),
                    "source": self.name
                })
            return results
        except Exception as e:
            print(f"[ERROR] {self.name}: {e}")
            return []


class BraveEngine(SearchEngine):
    """Brave 搜索引擎"""
    
    name = "brave"
    env_var = "BRAVE_API_KEY"
    
    def search(self, query: str, num_results: int = 15) -> List[Dict]:
        if not self.api_key:
            print(f"[WARNING] {self.name}: API key not configured")
            return []
        
        try:
            resp = requests.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={"X-Subscription-Token": self.api_key},
                params={"q": query, "count": num_results},
                timeout=30
            )
            resp.raise_for_status()
            data = resp.json()
            
            results = []
            for item in data.get("web", {}).get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "description": item.get("description", ""),
                    "source": self.name
                })
            return results
        except Exception as e:
            print(f"[ERROR] {self.name}: {e}")
            return []


class TavilyEngine(SearchEngine):
    """Tavily 搜索引擎"""
    
    name = "tavily"
    env_var = "TAVILY_API_KEY"
    
    def search(self, query: str, num_results: int = 15) -> List[Dict]:
        if not self.api_key:
            print(f"[WARNING] {self.name}: API key not configured")
            return []
        
        try:
            resp = requests.post(
                "https://api.tavily.com/search",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"query": query, "max_results": num_results},
                timeout=30
            )
            resp.raise_for_status()
            data = resp.json()
            
            results = []
            for item in data.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "description": item.get("content", ""),
                    "source": self.name
                })
            return results
        except Exception as e:
            print(f"[ERROR] {self.name}: {e}")
            return []


# ============================================================
# 工具函数
# ============================================================

def load_config(config_path: str) -> Dict:
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 展开环境变量
    def expand_env(obj):
        if isinstance(obj, str):
            if obj.startswith('${') and obj.endswith('}'):
                env_var = obj[2:-1]
                return os.environ.get(env_var, obj)
            return obj
        elif isinstance(obj, dict):
            return {k: expand_env(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [expand_env(item) for item in obj]
        return obj
    
    return expand_env(config)


def generate_url_hash(url: str) -> str:
    """生成 URL 哈希（用于去重）"""
    return hashlib.md5(url.encode()).hexdigest()[:12]


def extract_domain(url: str) -> str:
    """提取域名"""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except:
        return ""


def is_valid_url(url: str, exclude_keywords: List[str]) -> bool:
    """检查 URL 是否有效"""
    if not url:
        return False
    
    # 检查协议
    if not url.startswith(('http://', 'https://')):
        return False
    
    # 检查排除词
    domain = extract_domain(url).lower()
    for keyword in exclude_keywords:
        if keyword.lower() in domain:
            return False
    
    # 检查黑名单
    import re
    for pattern in BLACKLIST_PATTERNS:
        if re.search(pattern, url, re.IGNORECASE):
            return False
    
    return True


def detect_customer_type(title: str, description: str, url: str) -> str:
    """检测客户类型"""
    text = f"{title} {description} {url}".lower()
    
    for keyword, customer_type in DOMAIN_TYPE_MAP:
        if keyword in text:
            return customer_type
    
    return "Unknown"


def assign_tier(has_email: bool, has_phone: bool, customer_type: str) -> str:
    """分配 Tier"""
    if customer_type in ["Distributor", "Integrator"] and (has_email or has_phone):
        return "Tier 1"
    elif customer_type != "Unknown" and (has_email or has_phone):
        return "Tier 2"
    else:
        return "Tier 3"


def calculate_completeness(record: Dict) -> str:
    """计算完整度"""
    has_email = bool(record.get("email"))
    has_phone = bool(record.get("phone"))
    has_contact = bool(record.get("contact_person"))
    
    if has_email and has_phone and has_contact:
        return "✅ 完整"
    elif has_email or has_phone:
        return "⏳ 待补全"
    else:
        return "⚠️ 部分"


# ============================================================
# 搜索流程
# ============================================================

class B2BSearcher:
    """B2B 搜索器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.seen_urls = set()
        self.seen_hashes = set()
        
        # 初始化搜索引擎
        self.engines = []
        for engine_config in config.get("search", {}).get("engines", []):
            name = engine_config.get("name")
            priority = engine_config.get("priority", 99)
            
            engine_class = {
                "serper": SerperEngine,
                "brave": BraveEngine,
                "tavily": TavilyEngine,
            }.get(name)
            
            if engine_class:
                engine = engine_class()
                self.engines.append((priority, engine))
        
        # 按优先级排序
        self.engines.sort(key=lambda x: x[0])
    
    def generate_keywords(self, num_keywords: int) -> List[Tuple[str, str, str]]:
        """
        生成关键词组合
        返回: [(keyword, language, market), ...]
        """
        product = self.config.get("product", {})
        markets = self.config.get("markets", [])
        
        # 获取关键词
        keywords_by_lang = product.get("keywords", {})
        high_value = product.get("high_value_indicators", [])
        
        combinations = []
        
        for market in markets:
            market_name = market.get("name", "")
            countries = market.get("countries", [])
            languages = market.get("languages", [])
            
            for lang in languages:
                keywords = keywords_by_lang.get(lang, [])
                if not keywords:
                    continue
                
                for keyword in keywords:
                    for country in countries:
                        # 组合: keyword + country
                        combinations.append((f"{keyword} {country}", lang, market_name))
                        
                        # 组合: keyword + high_value_indicator + country
                        if high_value:
                            indicator = random.choice(high_value)
                            combinations.append(
                                (f"{keyword} {indicator} {country}", lang, market_name)
                            )
        
        # 随机选择
        if len(combinations) > num_keywords:
            combinations = random.sample(combinations, num_keywords)
        
        return combinations
    
    def search_keyword(self, keyword: str, num_results: int) -> List[Dict]:
        """使用搜索引擎搜索关键词"""
        for priority, engine in self.engines:
            results = engine.search(keyword, num_results)
            if results:
                print(f"[OK] {engine.name}: {keyword} → {len(results)} results")
                return results
        
        print(f"[FAIL] All engines failed: {keyword}")
        return []
    
    def process_result(self, result: Dict, keyword: str, lang: str, market: str) -> Optional[Dict]:
        """处理搜索结果"""
        url = result.get("url", "")
        
        # 去重
        url_hash = generate_url_hash(url)
        if url_hash in self.seen_hashes:
            return None
        self.seen_hashes.add(url_hash)
        
        # 验证 URL
        exclude_keywords = self.config.get("exclude", {}).get("keywords", [])
        if not is_valid_url(url, exclude_keywords):
            return None
        
        # 提取信息
        title = result.get("title", "")
        description = result.get("description", "")
        domain = extract_domain(url)
        
        # 检测客户类型
        customer_type = detect_customer_type(title, description, url)
        
        # 构建记录
        record = {
            "公司名": title.split(" - ")[0].strip() if " - " in title else title,
            "国家": "",  # 需要后续补全
            "城市": "",
            "网站": url,
            "域名": domain,
            "主营内容": description[:200] if description else "",
            "客户类型": customer_type,
            "邮箱": "",
            "电话": "",
            "WhatsApp": "",
            "联系人": "",
            "职位": "",
            "来源": result.get("source", ""),
            "Tier": "Tier 3",
            "完整度": "⚠️ 部分",
            "备注": f"搜索关键词: {keyword} | 市场: {market} | 语言: {lang}",
            "入库时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "url_hash": url_hash,
        }
        
        return record
    
    def run(self, num_keywords: Optional[int] = None) -> List[Dict]:
        """
        执行搜索
        
        Args:
            num_keywords: 搜索关键词数量（None 则使用配置）
        
        Returns:
            搜索结果列表
        """
        search_config = self.config.get("search", {})
        if num_keywords is None:
            num_keywords = search_config.get("daily_keywords", 10)
        
        num_results = search_config.get("results_per_keyword", 15)
        
        print(f"\n{'='*60}")
        print(f"B2B Lead Search - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        print(f"Keywords: {num_keywords} | Results/keyword: {num_results}")
        print(f"Engines: {[e[1].name for e in self.engines]}")
        print(f"{'='*60}\n")
        
        # 生成关键词
        combinations = self.generate_keywords(num_keywords)
        print(f"Generated {len(combinations)} keyword combinations\n")
        
        # 执行搜索
        all_records = []
        
        for i, (keyword, lang, market) in enumerate(combinations, 1):
            print(f"[{i}/{len(combinations)}] Searching: {keyword}")
            
            results = self.search_keyword(keyword, num_results)
            
            for result in results:
                record = self.process_result(result, keyword, lang, market)
                if record:
                    all_records.append(record)
            
            print(f"  → Total records: {len(all_records)}\n")
        
        # 汇总
        print(f"\n{'='*60}")
        print(f"Search Complete!")
        print(f"{'='*60}")
        print(f"Keywords searched: {len(combinations)}")
        print(f"Unique results: {len(all_records)}")
        print(f"Customer types:")
        
        type_counts = {}
        for r in all_records:
            t = r.get("客户类型", "Unknown")
            type_counts[t] = type_counts.get(t, 0) + 1
        
        for t, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            print(f"  - {t}: {count}")
        
        print(f"{'='*60}\n")
        
        return all_records


# ============================================================
# CLI 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="B2B Lead Search")
    parser.add_argument("--config", required=True, help="Config file path")
    parser.add_argument("--keywords", type=int, help="Number of keywords to search")
    parser.add_argument("--output", help="Output file path (JSON)")
    parser.add_argument("--dry-run", action="store_true", help="Generate keywords only")
    
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config)
    
    # 创建搜索器
    searcher = B2BSearcher(config)
    
    # Dry run: 只生成关键词
    if args.dry_run:
        num = args.keywords or config.get("search", {}).get("daily_keywords", 10)
        combinations = searcher.generate_keywords(num)
        print(f"\nGenerated {len(combinations)} keyword combinations:\n")
        for i, (kw, lang, market) in enumerate(combinations, 1):
            print(f"{i}. [{lang}] [{market}] {kw}")
        return
    
    # 执行搜索
    records = searcher.run(args.keywords)
    
    # 输出
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(records)} records to {args.output}")
    else:
        # 默认输出到 stdout
        print(json.dumps(records, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
