#!/usr/bin/env python3
"""
B2B Lead Generation - Feishu Output Module
飞书多维表格输出模块

用法：
    python feishu_writer.py --input leads.json --config my-product.yaml

配置文件需要包含：
    output.feishu.app_id
    output.feishu.app_secret
    output.feishu.app_token
    output.feishu.table_id
"""

import os
import json
import yaml
import requests
import argparse
import time
from typing import Dict, List, Optional
from datetime import datetime


# 默认输出字段
DEFAULT_FIELDS = [
    "公司名", "国家", "城市", "网站", "主营内容", "客户类型",
    "邮箱", "电话", "WhatsApp", "联系人", "职位",
    "来源", "Tier", "完整度", "备注", "入库时间"
]

# 飞书字段类型映射
FIELD_TYPE_MAP = {
    "公司名": 1,      # 文本
    "国家": 1,        # 文本（飞书已验证可接受任意文本）
    "城市": 1,        # 文本
    "网站": 1,        # 文本（URL）
    "主营内容": 1,    # 文本（多行）
    "客户类型": 3,    # 单选
    "邮箱": 1,        # 文本
    "电话": 1,        # 文本
    "WhatsApp": 1,    # 文本
    "联系人": 1,      # 文本
    "职位": 1,        # 文本
    "来源": 3,        # 单选
    "Tier": 3,        # 单选
    "完整度": 3,      # 单选
    "备注": 1,        # 文本（多行）
    "入库时间": 5,    # 日期
}


class FeishuWriter:
    """飞书多维表格输出器"""
    
    def __init__(self, config: Dict):
        self.config = config
        feishu_config = config.get("output", {}).get("feishu", {})
        
        self.app_id = feishu_config.get("app_id") or os.environ.get("FEISHU_APP_ID")
        self.app_secret = feishu_config.get("app_secret") or os.environ.get("FEISHU_APP_SECRET")
        self.app_token = feishu_config.get("app_token")
        self.table_id = feishu_config.get("table_id")
        
        self.tenant_token = None
        self.token_expires = 0
        
        self.base_url = "https://open.feishu.cn/open-apis"
        
        if not all([self.app_id, self.app_secret, self.app_token, self.table_id]):
            raise ValueError("Missing Feishu configuration. Check config file or environment variables.")
    
    def get_tenant_token(self) -> str:
        """获取 tenant_access_token"""
        if self.tenant_token and time.time() < self.token_expires - 60:
            return self.tenant_token
        
        resp = requests.post(
            f"{self.base_url}/auth/v3/tenant_access_token/internal",
            json={
                "app_id": self.app_id,
                "app_secret": self.app_secret
            },
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        
        if data.get("code") != 0:
            raise ValueError(f"Feishu auth failed: {data}")
        
        self.tenant_token = data["tenant_access_token"]
        self.token_expires = time.time() + data.get("expire", 7200)
        
        return self.tenant_token
    
    def get_headers(self) -> Dict:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.get_tenant_token()}",
            "Content-Type": "application/json"
        }
    
    def list_records(self, filter_str: str = None) -> List[Dict]:
        """查询记录"""
        params = {"table_id": self.table_id}
        if filter_str:
            params["filter"] = filter_str
        
        resp = requests.get(
            f"{self.base_url}/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records",
            headers=self.get_headers(),
            params=params,
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        
        if data.get("code") != 0:
            print(f"[FEISHU] Error: {data}")
            return []
        
        return data.get("data", {}).get("items", [])
    
    def insert_record(self, record: Dict) -> Optional[str]:
        """
        插入单条记录
        
        Returns:
            记录 ID 或 None
        """
        # 构建 fields
        fields = {}
        for key in DEFAULT_FIELDS:
            value = record.get(key)
            if value is None:
                continue
            
            field_type = FIELD_TYPE_MAP.get(key, 1)
            
            # 单选字段
            if field_type == 3:
                fields[key] = {"text": value}
            # 日期字段
            elif field_type == 5:
                # ISO 格式转换
                if isinstance(value, str):
                    # 2024-01-01 12:00:00 → 2024-01-01
                    fields[key] = int(datetime.strptime(value.split()[0], "%Y-%m-%d").timestamp() * 1000)
            else:
                fields[key] = str(value)
        
        resp = requests.post(
            f"{self.base_url}/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records",
            headers=self.get_headers(),
            json={"records": [{"fields": fields}]},
            timeout=30
        )
        
        data = resp.json()
        if data.get("code") != 0:
            print(f"[FEISHU] Insert failed: {data.get('msg', data)}")
            return None
        
        return data.get("data", {}).get("records", [{}])[0].get("record_id")
    
    def batch_insert(self, records: List[Dict], batch_size: int = 10) -> int:
        """
        批量插入（分批次）
        
        Returns:
            成功插入的记录数
        """
        success = 0
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            
            # 构建 fields
            batch_records = []
            for record in batch:
                fields = {}
                for key in DEFAULT_FIELDS:
                    value = record.get(key)
                    if value is None:
                        continue
                    
                    field_type = FIELD_TYPE_MAP.get(key, 1)
                    
                    if field_type == 3:
                        fields[key] = {"text": value}
                    elif field_type == 5:
                        if isinstance(value, str):
                            fields[key] = int(datetime.strptime(value.split()[0], "%Y-%m-%d").timestamp() * 1000)
                    else:
                        fields[key] = str(value)
                
                batch_records.append({"fields": fields})
            
            resp = requests.post(
                f"{self.base_url}/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records",
                headers=self.get_headers(),
                json={"records": batch_records},
                timeout=60
            )
            
            data = resp.json()
            if data.get("code") != 0:
                print(f"[FEISHU] Batch insert failed: {data.get('msg', data)}")
                # 逐条插入
                for record in batch:
                    if self.insert_record(record):
                        success += 1
            else:
                success += len(batch)
        
        return success
    
    def write(self, records: List[Dict]) -> int:
        """
        写入记录（去重）
        
        Returns:
            成功写入的记录数
        """
        if not records:
            print("[FEISHU] No records to write")
            return 0
        
        # 获取已有记录的 URL
        print("[FEISHU] Checking existing records...")
        existing_urls = set()
        
        # 分页查询
        has_more = True
        page_token = None
        
        while has_more:
            params = {"table_id": self.table_id, "page_size": 100}
            if page_token:
                params["page_token"] = page_token
            
            resp = requests.get(
                f"{self.base_url}/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records",
                headers=self.get_headers(),
                params=params,
                timeout=30
            )
            
            data = resp.json()
            if data.get("code") != 0:
                print(f"[FEISHU] Query failed: {data}")
                break
            
            items = data.get("data", {}).get("items", [])
            for item in items:
                fields = item.get("fields", {})
                url = fields.get("网站", "")
                if url:
                    existing_urls.add(url.lower())
            
            has_more = data.get("data", {}).get("has_more", False)
            page_token = data.get("data", {}).get("page_token")
        
        print(f"[FEISHU] Found {len(existing_urls)} existing URLs")
        
        # 过滤重复
        new_records = []
        for record in records:
            url = record.get("网站", "").strip().lower()
            if url and url not in existing_urls:
                new_records.append(record)
                existing_urls.add(url)
        
        if not new_records:
            print(f"[FEISHU] All {len(records)} records are duplicates, skipped")
            return 0
        
        # 写入
        print(f"[FEISHU] Writing {len(new_records)} new records...")
        success = self.batch_insert(new_records)
        
        print(f"[FEISHU] Successfully inserted {success}/{len(new_records)} records")
        if len(new_records) < len(records):
            print(f"[FEISHU] Skipped {len(records) - len(new_records)} duplicates")
        
        return success


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


def main():
    parser = argparse.ArgumentParser(description="B2B Lead Feishu Writer")
    parser.add_argument("--input", required=True, help="Input JSON file")
    parser.add_argument("--config", required=True, help="Config YAML file")
    
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config)
    
    # 加载记录
    with open(args.input, 'r', encoding='utf-8') as f:
        records = json.load(f)
    
    # 写入飞书
    writer = FeishuWriter(config)
    writer.write(records)


if __name__ == "__main__":
    main()