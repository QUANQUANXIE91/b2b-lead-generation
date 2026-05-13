#!/usr/bin/env python3
"""
B2B Lead Generation - CSV Output Module
CSV 输出模块

用法：
    python csv_writer.py --input leads.json --output ./leads.csv
"""

import os
import json
import csv
import argparse
from datetime import datetime
from typing import Dict, List


# 默认输出字段
DEFAULT_FIELDS = [
    "公司名", "国家", "城市", "网站", "主营内容", "客户类型",
    "邮箱", "电话", "WhatsApp", "联系人", "职位",
    "来源", "Tier", "完整度", "备注", "入库时间"
]


class CSVWriter:
    """CSV 输出器"""
    
    def __init__(self, output_path: str, fields: List[str] = None, append: bool = True):
        self.output_path = output_path
        self.fields = fields or DEFAULT_FIELDS
        self.append = append
        
        # 确保目录存在
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    
    def write(self, records: List[Dict]) -> int:
        """
        写入记录
        
        Returns:
            成功写入的记录数
        """
        if not records:
            print("[CSV] No records to write")
            return 0
        
        # 检查文件是否存在
        file_exists = os.path.exists(self.output_path)
        
        # 确定模式
        mode = 'a' if self.append and file_exists else 'w'
        
        # 去重：读取已有 URL
        existing_urls = set()
        if self.append and file_exists:
            try:
                with open(self.output_path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if "网站" in row:
                            existing_urls.add(row["网站"].strip().lower())
            except Exception as e:
                print(f"[CSV] Warning: Could not read existing file: {e}")
        
        # 过滤重复
        new_records = []
        for record in records:
            url = record.get("网站", "").strip().lower()
            if url and url not in existing_urls:
                new_records.append(record)
                existing_urls.add(url)
        
        if not new_records:
            print(f"[CSV] All {len(records)} records are duplicates, skipped")
            return 0
        
        # 写入
        with open(self.output_path, mode, encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.fields, extrasaction='ignore')
            
            # 写入表头（仅新文件或覆盖模式）
            if mode == 'w':
                writer.writeheader()
            
            for record in new_records:
                writer.writerow(record)
        
        print(f"[CSV] Written {len(new_records)} records to {self.output_path}")
        if len(new_records) < len(records):
            print(f"[CSV] Skipped {len(records) - len(new_records)} duplicates")
        
        return len(new_records)
    
    def read_all(self) -> List[Dict]:
        """读取所有记录"""
        if not os.path.exists(self.output_path):
            return []
        
        with open(self.output_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            return list(reader)


def main():
    parser = argparse.ArgumentParser(description="B2B Lead CSV Writer")
    parser.add_argument("--input", required=True, help="Input JSON file")
    parser.add_argument("--output", required=True, help="Output CSV file")
    parser.add_argument("--append", action="store_true", default=True, help="Append mode")
    parser.add_argument("--fields", nargs='+', help="Custom fields")
    
    args = parser.parse_args()
    
    # 加载记录
    with open(args.input, 'r', encoding='utf-8') as f:
        records = json.load(f)
    
    # 写入
    writer = CSVWriter(
        args.output,
        fields=args.fields,
        append=args.append
    )
    writer.write(records)


if __name__ == "__main__":
    main()
