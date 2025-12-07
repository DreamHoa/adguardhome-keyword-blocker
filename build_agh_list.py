import requests
from datetime import datetime
import re
import os

# ================= 配置区域 =================
TARGET_FILE = "target_sites.txt"
OUTPUT_AGH_LIST = "adguardhome_blocklist.txt"
# ===========================================

BASE_URL = "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/"

def fetch_and_parse_site(site_name):
    """
    下载并解析指定站点的域名列表，严格跳过 'include:' 关联指令。
    """
    print(f"Fetching domains strictly for: {site_name}...")
    
    try:
        url = BASE_URL + site_name
        resp = requests.get(url, timeout=10)
        
        if resp.status_code != 200:
            print(f"⚠️ Warning: Site data for {site_name} not found or inaccessible.")
            return []
            
        lines = resp.text.split('\n')
        domains = []
        
        for line in lines:
            line = line.strip()
            # 忽略注释、空行和 'include:' 关联指令 (严格执行用户不关联的要求)
            if not line or line.startswith('#') or line.startswith('include:'):
                continue
                
            # 提取纯域名 (处理 'full:', 'domain:', 'keyword:' 等前缀)
            clean_domain = line
            if ':' in line:
                parts = line.split(':')
                # 只处理常用的 domain/full/keyword 类型
                if parts[0] in ['domain', 'full', 'keyword']:
                    clean_domain = parts[1]
                else:
                    continue # 跳过复杂的正则
            
            # 移除可能存在的 @Attributes 和 IP 地址
            if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', clean_domain):
                continue
            if '@' in clean_domain:
                clean_domain = clean_domain.split('@')[0]
            
            # 最终检查，确保是有效的域名
            if clean_domain:
                domains.append(clean_domain)
            
        return domains
    except Exception as e:
        print(f"Error fetching site {site_name}: {e}")
        return []

def main():
    if not os.path.exists(TARGET_FILE):
        print(f"Error: Target file {TARGET_FILE} not found.")
        return

    # 1. 读取用户指定的关键词列表
    with open(TARGET_FILE, 'r') as f:
        target_sites = [line.strip().lower() for line in f if line.strip() and not line.startswith('#')]

    if not target_sites:
        print("No target sites specified. Exiting.")
        return
        
    final_domains = set()
    for site in target_sites:
        domains = fetch_and_parse_site(site)
        final_domains.update(domains)
    
    # 2. 生成 AdGuard Home 兼容列表 (纯域名，一行一个)
    agh_lines = [
        f"# AdGuard Home Blocklist for: {', '.join(target_sites)}",
        "# Source: v2fly/domain-list-community (Strict Keyword Matching)",
        f"# Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    ]
    
    for domain in sorted(final_domains):
        agh_lines.append(domain)
    
    with open(OUTPUT_AGH_LIST, 'w', encoding='utf-8') as f:
        f.write("\n".join(agh_lines))
    print(f"✅ Successfully generated {OUTPUT_AGH_LIST} with {len(final_domains)} domains.")

if __name__ == "__main__":
    # 需要 requests 库
    main()
