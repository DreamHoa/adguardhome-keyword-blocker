import requests
import os

# ================= 配置 =================
# 你的关键词文件
INPUT_FILE = "target_sites.txt"
# 输出给 AdGuard Home 的文件
OUTPUT_FILE = "adguardhome_blocklist.txt"
# 上游数据源 (v2fly 社区版)
BASE_URL = "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/"

def get_targets():
    """读取 targets.txt 中的关键词"""
    if not os.path.exists(INPUT_FILE):
        print(f"错误: 找不到 {INPUT_FILE}")
        return []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        # 过滤空行和注释
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

def fetch_and_parse(keyword):
    """下载并严格解析规则（丢弃关联域名）"""
    url = BASE_URL + keyword
    print(f"正在抓取: {keyword} ...")
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"  -> 失败: 远程仓库没有找到关键词 '{keyword}' (404)")
            return []
            
        lines = response.text.splitlines()
        valid_rules = []
        
        for line in lines:
            # 1. 清理空格和行内注释
            line = line.split('#')[0].strip()
            if not line:
                continue
                
            # 2. 【核心修改】严格过滤：丢弃所有 include 引用
            # 如果这行是 include:xxx，说明它是关联域名，按照你的要求：不要！
            if line.startswith("include:"):
                continue
            
            # 3. 丢弃正则和属性行 (AdGuard Home 基础模式通常不需要)
            if line.startswith("regexp:") or line.startswith("keyword:") or line.startswith("@"):
                continue

            # 4. 格式转换
            if line.startswith("full:"):
                # 精确匹配 -> |domain.com^
                domain = line.replace("full:", "")
                valid_rules.append(f"|{domain}^")
            else:
                # 泛域名匹配 -> ||domain.com^
                valid_rules.append(f"||{line}^")
                
        return valid_rules

    except Exception as e:
        print(f"  -> 错误: {e}")
        return []

def main():
    targets = get_targets()
    if not targets:
        print("没有指定任何 Target，脚本结束。")
        return

    all_rules = set()
    
    for keyword in targets:
        rules = fetch_and_parse(keyword)
        if rules:
            print(f"  -> 获取到 {len(rules)} 条规则")
            all_rules.update(rules)
    
    # 排序并写入
    sorted_rules = sorted(list(all_rules))
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(f"! Title: Custom Social Blocklist\n")
        f.write(f"! Description: Strict mode (No includes). Keywords: {', '.join(targets)}\n")
        f.write(f"! Count: {len(sorted_rules)}\n")
        f.write(f"! Updated: {os.popen('date -u').read().strip()}\n")
        f.write("\n")
        for rule in sorted_rules:
            f.write(rule + "\n")
            
    print(f"\n========================================")
    print(f"处理完成！共生成 {len(sorted_rules)} 条规则。")
    print(f"已保存到: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
