import os
import re
import requests
from datetime import datetime
from collections import defaultdict

# 基础路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
TEMP_DIR = os.path.join(DATA_DIR, "python")
RULE_DIR = os.path.join(DATA_DIR, "rules")

# 多源配置（支持镜像站自动回退）
HOSTS_SOURCES = [
    "https://raw.githubusercontent.com/jdlingyu/ad-wars/master/hosts",
    "https://raw.githubusercontent.com/lingeringsound/10007_auto/master/reward",
    "https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/Filters/AWAvenue-Ads-Rule-hosts.txt"
]

MIRROR_PROXIES = [
    "https://ghproxy.net/",
    "https://ghfast.top/",
    "https://raw.gitmirror.com/"
]

# 调试输出
print(f"[DEBUG] 工作目录: {BASE_DIR}")
print(f"[DEBUG] 数据存储路径: {DATA_DIR}")

def ensure_directory(path):
    """确保目标目录存在"""
    dir_path = os.path.dirname(path)
    os.makedirs(dir_path, exist_ok=True)
    print(f"✓ 已创建目录: {dir_path}")

def download_with_retry(url, retries=3):
    """带镜像回退的下载器"""
    for attempt in range(retries):
        try:
            # 优先尝试直连
            if attempt == 0:
                resp = requests.get(url, timeout=10)
            # 失败后使用镜像站
            else:
                proxy = MIRROR_PROXIES[attempt % len(MIRROR_PROXIES)]
                resp = requests.get(f"{proxy}{url}", timeout=15)
            
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            print(f"第 {attempt+1} 次下载失败: {str(e)}")
            if attempt == retries - 1:
                raise

def download_hosts():
    """下载多源hosts文件"""
    downloaded_files = []
    
    for index, url in enumerate(HOSTS_SOURCES):
        try:
            content = download_with_retry(url)
            filename = f"hosts_{index}_{datetime.now().strftime('%Y%m%d')}.txt"
            save_path = os.path.join(TEMP_DIR, filename)
            
            ensure_directory(save_path)
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"↓ 已下载: {url} => {save_path}")
            downloaded_files.append(save_path)
        except Exception as e:
            print(f"× 下载失败 [{url}]: {str(e)}")
            continue
    
    return downloaded_files

def merge_hosts_files(file_paths):
    """合并并去重hosts条目"""
    entry_pattern = re.compile(
        r"^\s*((?:[0-9]{1,3}\.){3}[0-9]{1,3}|::1)\s+([a-zA-Z0-9\.-]+)\s*(?:#.*)?$"
    )
    
    domain_map = defaultdict(list)
    preserved_comments = []
    unique_ips = set()

    # 第一阶段：收集所有条目
    for file_path in file_paths:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    # 保留文件头注释
                    if line.startswith("#"):
                        if len(preserved_comments) < 5:
                            preserved_comments.append(line)
                        continue
                    
                    # 解析有效条目
                    match = entry_pattern.match(line)
                    if match:
                        ip, domain = match.groups()
                        domain = domain.lower()
                        
                        # 记录唯一IP
                        if ip not in unique_ips:
                            unique_ips.add(ip)
                        
                        # 冲突处理：记录最后出现的IP
                        domain_map[domain].append(ip)
        except Exception as e:
            print(f"× 文件处理错误 [{file_path}]: {str(e)}")
            continue

    # 第二阶段：生成合并结果
    merged_content = []
    
    # 添加保留注释
    merged_content.extend(preserved_comments)
    
    # 添加IP注释统计
    merged_content.append(f"# Merged at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    merged_content.append(f"# Total unique IPs: {len(unique_ips)}")
    merged_content.append(f"# Total domains: {len(domain_map)}\n")
    
    # 按字母顺序排序输出
    for domain in sorted(domain_map.keys()):
        ips = domain_map[domain]
        # 使用最后出现的IP地址
        merged_content.append(f"{ips[-1]}\t{domain}")
    
    return merged_content

def main():
    print("\n=== 同步流程开始 ===")
    
    # 下载阶段
    print("\n[阶段1] 下载源文件")
    hosts_files = download_hosts()
    if not hosts_files:
        print("! 错误: 未成功下载任何文件")
        return
    
    # 合并阶段
    print("\n[阶段2] 合并处理")
    output_path = os.path.join(RULE_DIR, "merged_hosts.txt")
    ensure_directory(output_path)
    
    merged_data = merge_hosts_files(hosts_files)
    
    # 写入最终文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(merged_data))
    
    print(f"\n★ 同步完成: 生成 {len(merged_data)-4} 条规则（已保存至 {output_path}）")

if __name__ == "__main__":
    main()
