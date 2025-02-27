import os
import requests
import re
from datetime import datetime
from collections import defaultdict

# 基础路径配置（全部使用相对路径）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
TEMP_DIR = os.path.join(DATA_DIR, "python")
RULE_DIR = os.path.join(DATA_DIR, "rules")

# 下载源配置
HOSTS_SOURCES = [
    "https://raw.githubusercontent.com/jdlingyu/ad-wars/master/hosts",
    "https://raw.githubusercontent.com/lingeringsound/10007_auto/master/reward",
    "https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/Filters/AWAvenue-Ads-Rule-hosts.txt",
"https://raw.githubusercontent.com/ineo6/hosts/refs/heads/master/hosts"
]

def ensure_directory(path):
    """确保目录存在"""
    dir_path = os.path.dirname(path)
    os.makedirs(dir_path, exist_ok=True)
    print(f"[目录已创建] {dir_path}")

def download_hosts():
    """下载多源hosts文件"""
    downloaded_files = []
    for index, url in enumerate(HOSTS_SOURCES):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            filename = f"hosts_{index}.txt"
            save_path = os.path.join(TEMP_DIR, filename)
            
            ensure_directory(save_path)
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            print(f"[下载成功] {url} → {save_path}")
            downloaded_files.append(save_path)
        except Exception as e:
            print(f"[下载失败] {url} - {str(e)}")
            continue
    return downloaded_files

def merge_hosts(files):
    """合并去重逻辑"""
    entry_pattern = re.compile(r'^\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+(\S+)')
    domain_map = {}
    
    for file_path in files:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                match = entry_pattern.match(line)
                if match:
                    ip, domain = match.groups()
                    domain_map[domain.lower()] = ip  # 最后出现的IP会覆盖之前的
    
    return domain_map

def main():
    print("\n=== 开始同步流程 ===")
    
    # 步骤1: 下载文件
    print("\n[阶段1] 下载源文件")
    hosts_files = download_hosts()
    if not hosts_files:
        print("错误: 未下载到任何有效文件")
        return
    
    # 步骤2: 合并去重
    print("\n[阶段2] 合并处理")
    merged_data = merge_hosts(hosts_files)
    
    # 步骤3: 生成最终文件
    output_path = os.path.join(RULE_DIR, "merged_hosts.txt")
    ensure_directory(output_path)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# 最后更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("# 项目地址: https://github.com/045200/hyper_hosts\n\n")
        for domain, ip in sorted(merged_data.items()):
            f.write(f"{ip}\t{domain}\n")
    
    print(f"\n=== 同步完成 ===")
    print(f"生成文件: {output_path}")
    print(f"规则总数: {len(merged_data)}")

if __name__ == "__main__":
    main()
