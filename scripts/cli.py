#!/usr/bin/env python3
"""
B2B Lead Generation - CLI Entry Point
统一命令行入口

用法：
    b2b-lead init --config my-product.yaml
    b2b-lead search --config my-product.yaml
    b2b-lead enrich --config my-product.yaml
    b2b-lead report
    b2b-lead run --config my-product.yaml
"""

import os
import sys
import json
import yaml
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

# 获取脚本目录
SCRIPT_DIR = Path(__file__).parent.resolve()
CORE_DIR = SCRIPT_DIR / "core"
OUTPUT_DIR = SCRIPT_DIR / "outputs"
SKILL_DIR = SCRIPT_DIR.parent.resolve()


def load_config(config_path: str) -> dict:
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def expand_env(obj):
    """展开环境变量"""
    if isinstance(obj, str) and obj.startswith('${') and obj.endswith('}'):
        return os.environ.get(obj[2:-1], obj)
    elif isinstance(obj, dict):
        return {k: expand_env(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [expand_env(item) for item in obj]
    return obj


def cmd_init(args):
    """初始化配置"""
    print("\n" + "="*60)
    print("B2B Lead Generation - Init")
    print("="*60 + "\n")
    
    # 检查配置文件
    config_path = args.config
    if not os.path.exists(config_path):
        # 从模板复制
        template = SKILL_DIR / "config.example.yaml"
        if template.exists():
            print(f"[INFO] Creating config from template: {template}")
            with open(template, 'r') as f:
                content = f.read()
            with open(config_path, 'w') as f:
                f.write(content)
            print(f"[OK] Created: {config_path}")
            print("\n请编辑配置文件，填入你的产品关键词和目标市场:")
            print(f"  nano {config_path}")
        else:
            print(f"[ERROR] Template not found: {template}")
            return 1
    
    # 加载配置
    config = load_config(config_path)
    
    # 验证配置
    product = config.get("product", {})
    if not product.get("keywords"):
        print("[WARN] No keywords configured. Please add keywords to config.")
        return 1
    
    output = config.get("output", {})
    output_type = output.get("type", "csv")
    
    # 初始化输出
    if output_type == "csv":
        csv_path = output.get("csv", {}).get("path", "./leads.csv")
        print(f"[OK] Output type: CSV ({csv_path})")
    
    elif output_type == "feishu":
        print("[OK] Output type: Feishu")
        feishu = output.get("feishu", {})
        if not feishu.get("app_token") or not feishu.get("table_id"):
            print("[WARN] Missing Feishu app_token or table_id")
            print("       请在配置文件中填入飞书多维表格的 app_token 和 table_id")
        else:
            print(f"       App Token: {feishu.get('app_token')[:10]}...")
            print(f"       Table ID: {feishu.get('table_id')}")
    
    print("\n[OK] Configuration ready!")
    print("\n下一步:")
    print(f"  b2b-lead search --config {config_path}")
    
    return 0


def cmd_search(args):
    """执行搜索"""
    print("\n" + "="*60)
    print("B2B Lead Generation - Search")
    print("="*60 + "\n")
    
    config_path = args.config
    
    # 执行搜索脚本
    search_script = CORE_DIR / "search.py"
    
    cmd = [
        sys.executable,
        str(search_script),
        "--config", config_path,
        "--keywords", str(args.keywords or 10),
    ]
    
    # 临时输出文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = f"/tmp/b2b_search_{timestamp}.json"
    cmd.extend(["--output", output_json])
    
    print(f"[CMD] {cmd[0]} {cmd[1]} {cmd[2]} {cmd[3]} {cmd[4]} {cmd[5]} {cmd[6]}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    if result.returncode != 0:
        print(f"[ERROR] Search failed: {result.returncode}")
        return result.returncode
    
    # 加载搜索结果
    if os.path.exists(output_json):
        with open(output_json, 'r') as f:
            records = json.load(f)
        
        print(f"\n[OK] Found {len(records)} records")
        print(f"[INFO] Saved to: {output_json}")
        
        # 输出到目标
        config = load_config(config_path)
        output_type = config.get("output", {}).get("type", "csv")
        
        if output_type == "csv":
            csv_writer = OUTPUT_DIR / "csv_writer.py"
            csv_path = config.get("output", {}).get("csv", {}).get("path", "./leads.csv")
            
            subprocess.run([
                sys.executable, str(csv_writer),
                "--input", output_json,
                "--output", csv_path
            ])
        
        elif output_type == "feishu":
            feishu_writer = OUTPUT_DIR / "feishu_writer.py"
            
            subprocess.run([
                sys.executable, str(feishu_writer),
                "--input", output_json,
                "--config", config_path
            ])
    
    return 0


def cmd_enrich(args):
    """补全联系方式"""
    print("\n" + "="*60)
    print("B2B Lead Generation - Enrich")
    print("="*60 + "\n")
    
    config_path = args.config
    
    # 获取输入文件
    config = load_config(config_path)
    output_type = config.get("output", {}).get("type", "csv")
    
    if output_type == "csv":
        csv_path = config.get("output", {}).get("csv", {}).get("path", "./leads.csv")
        
        # 读取 CSV 并转换为 JSON
        import csv
        records = []
        if os.path.exists(csv_path):
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                records = list(reader)
        
        if not records:
            print(f"[ERROR] No records found in {csv_path}")
            return 1
        
        # 保存为临时 JSON
        input_json = "/tmp/b2b_enrich_input.json"
        with open(input_json, 'w') as f:
            json.dump(records, f, ensure_ascii=False)
    
    else:
        # 从飞书读取
        print("[WARN] Feishu enrich requires reading from Feishu API")
        print("       请先导出飞书数据为 CSV，再运行补全")
        return 1
    
    # 执行补全脚本
    enrich_script = CORE_DIR / "enrich.py"
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = f"/tmp/b2b_enrich_{timestamp}.json"
    
    cmd = [
        sys.executable,
        str(enrich_script),
        "--config", config_path,
        "--input", input_json,
        "--output", output_json,
        "--limit", str(args.limit or 50),
    ]
    
    print(f"[CMD] Running enrich...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    if result.returncode != 0:
        print(f"[ERROR] Enrich failed: {result.returncode}")
        return result.returncode
    
    # 更新 CSV
    if output_type == "csv" and os.path.exists(output_json):
        csv_path = config.get("output", {}).get("csv", {}).get("path", "./leads.csv")
        
        # 读取补全后的记录
        with open(output_json, 'r') as f:
            enriched = json.load(f)
        
        # 写入 CSV（覆盖）
        import csv
        with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
            fields = enriched[0].keys() if enriched else []
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(enriched)
        
        print(f"[OK] Updated {csv_path}")
    
    return 0


def cmd_report(args):
    """生成反思报告"""
    print("\n" + "="*60)
    print("B2B Lead Generation - Report")
    print("="*60 + "\n")
    
    # 检查 skill_meta.json
    meta_path = SKILL_DIR / "skill_meta.json"
    
    if not meta_path.exists():
        print("[INFO] No reflection data yet. Run some searches first.")
        return 0
    
    with open(meta_path, 'r') as f:
        meta = json.load(f)
    
    print(f"Version: {meta.get('version', 'N/A')}")
    print(f"Utility Score: {meta.get('utility_score', 0):.2f}")
    print(f"Total Executions: {meta.get('total_executions', 0)}")
    print(f"Success Rate: {meta.get('success_rate', 0):.1f}%")
    
    # 最近执行记录
    logs = meta.get("execution_logs", [])
    if logs:
        print(f"\nRecent Executions ({len(logs)}):")
        for log in logs[-5:]:
            print(f"  - {log.get('timestamp')}: {log.get('stage')} - {log.get('status')}")
    
    # 进化建议
    suggestions = meta.get("evolution_suggestions", [])
    if suggestions:
        print(f"\nEvolution Suggestions ({len(suggestions)}):")
        for s in suggestions[:3]:
            print(f"  - [{s.get('priority')}] {s.get('suggestion')}")
    
    return 0


def cmd_run(args):
    """一键运行全部流程"""
    print("\n" + "="*60)
    print("B2B Lead Generation - Full Run")
    print("="*60 + "\n")
    
    config_path = args.config
    
    # 1. 搜索
    print("\n[1/2] Searching...")
    ret = cmd_search(args)
    if ret != 0:
        return ret
    
    # 2. 补全
    print("\n[2/2] Enriching...")
    ret = cmd_enrich(args)
    if ret != 0:
        return ret
    
    print("\n" + "="*60)
    print("[OK] Full run complete!")
    print("="*60 + "\n")
    
    return 0


def cmd_stats(args):
    """显示统计"""
    print("\n" + "="*60)
    print("B2B Lead Generation - Stats")
    print("="*60 + "\n")
    
    config_path = args.config
    config = load_config(config_path)
    
    output_type = config.get("output", {}).get("type", "csv")
    
    if output_type == "csv":
        csv_path = config.get("output", {}).get("csv", {}).get("path", "./leads.csv")
        
        if not os.path.exists(csv_path):
            print(f"[INFO] No data file: {csv_path}")
            return 0
        
        import csv
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            records = list(reader)
        
        print(f"Total Records: {len(records)}")
        
        # 统计
        countries = {}
        types = {}
        tiers = {}
        completeness = {}
        
        for r in records:
            c = r.get("国家", "Unknown")
            countries[c] = countries.get(c, 0) + 1
            
            t = r.get("客户类型", "Unknown")
            types[t] = types.get(t, 0) + 1
            
            tier = r.get("Tier", "Tier 3")
            tiers[tier] = tiers.get(tier, 0) + 1
            
            comp = r.get("完整度", "⚠️ 部分")
            completeness[comp] = completeness.get(comp, 0) + 1
        
        print(f"\nTop Countries:")
        for c, count in sorted(countries.items(), key=lambda x: -x[1])[:10]:
            print(f"  {c}: {count}")
        
        print(f"\nCustomer Types:")
        for t, count in sorted(types.items(), key=lambda x: -x[1]):
            print(f"  {t}: {count}")
        
        print(f"\nTiers:")
        for tier, count in sorted(tiers.items()):
            print(f"  {tier}: {count}")
        
        print(f"\nCompleteness:")
        for comp, count in sorted(completeness.items()):
            print(f"  {comp}: {count}")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="B2B Lead Generation CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # init
    p_init = subparsers.add_parser("init", help="Initialize configuration")
    p_init.add_argument("--config", default="my-product.yaml", help="Config file")
    p_init.set_defaults(func=cmd_init)
    
    # search
    p_search = subparsers.add_parser("search", help="Search for leads")
    p_search.add_argument("--config", required=True, help="Config file")
    p_search.add_argument("--keywords", type=int, default=10, help="Keywords to search")
    p_search.set_defaults(func=cmd_search)
    
    # enrich
    p_enrich = subparsers.add_parser("enrich", help="Enrich contacts")
    p_enrich.add_argument("--config", required=True, help="Config file")
    p_enrich.add_argument("--limit", type=int, default=50, help="Max records")
    p_enrich.set_defaults(func=cmd_enrich)
    
    # report
    p_report = subparsers.add_parser("report", help="Reflection report")
    p_report.set_defaults(func=cmd_report)
    
    # run
    p_run = subparsers.add_parser("run", help="Full run (search + enrich)")
    p_run.add_argument("--config", required=True, help="Config file")
    p_run.add_argument("--keywords", type=int, default=10, help="Keywords to search")
    p_run.add_argument("--limit", type=int, default=50, help="Enrich limit")
    p_run.set_defaults(func=cmd_run)
    
    # stats
    p_stats = subparsers.add_parser("stats", help="Show statistics")
    p_stats.add_argument("--config", required=True, help="Config file")
    p_stats.set_defaults(func=cmd_stats)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 0
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())