import os
import requests
import re
from datetime import datetime

# 基础路径配置（全部使用相对路径）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
TEMP_DIR = os.path.join(DATA_DIR, "python")
RULE_DIR = os.path.join(DATA_DIR, "rules")

# 下载源配置
HOSTS_SOURCES = [
    "https://raw.githubusercontent.com/lingeringsound/10007_auto/master/all",
    "https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/Filters/AWAvenue-Ads-Rule-hosts.txt",
    "https://raw.hellogithub.com/hosts"
]

# 白名单源配置，与HOSTS_SOURCES一致
WHITE_LIST_SOURCES = [
    "https://raw.githubusercontent.com/lingeringsound/10007_auto/master/Adaway_white_list.prop"
    # 你可以在此扩展更多白名单源，格式与 Adaway 一致
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

def download_white_list():
    """下载白名单文件（多源）"""
    downloaded_files = []
    for index, url in enumerate(WHITE_LIST_SOURCES):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            filename = f"whitelist_{index}.txt"
            save_path = os.path.join(TEMP_DIR, filename)

            ensure_directory(save_path)
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(response.text)

            print(f"[白名单下载成功] {url} → {save_path}")
            downloaded_files.append(save_path)
        except Exception as e:
            print(f"[白名单下载失败] {url} - {str(e)}")
            continue
    return downloaded_files

def merge_white_list(files):
    """合并去重白名单（支持Adaway格式，保留注释头）"""
    domain_set = set()
    comment_lines = []
    is_header = True
    entry_pattern = re.compile(r'^([a-zA-Z0-9\-\.\*_?]+)$')  # 允许通配符

    for file_path in files:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                raw_line = line.rstrip('\n')
                line = raw_line.strip()
                if not line:
                    if is_header:
                        comment_lines.append('')
                    continue
                if line.startswith('#'):
                    if is_header:
                        comment_lines.append(raw_line)
                    continue
                else:
                    is_header = False  # 遇到第一个有效域名后不再记录注释头
                    # 只收集有效域名行
                    m = entry_pattern.match(line)
                    if m:
                        domain_set.add(line.lower())

    return comment_lines, domain_set

def main():
    print("\n=== 开始同步流程 ===")

    # 阶段1: 下载文件
    print("\n[阶段1] 下载源文件")
    hosts_files = download_hosts()
    if not hosts_files:
        print("错误: 未下载到任何有效文件")
        return

    # 添加本地hosts.txt
    local_hosts_path = os.path.join(TEMP_DIR, "hosts.txt")
    if os.path.isfile(local_hosts_path):
        hosts_files.append(local_hosts_path)
        print(f"[添加本地文件] {local_hosts_path}")
    else:
        print(f"[警告] 本地文件 {local_hosts_path} 不存在，已跳过")

    # 阶段2: 合并处理
    print("\n[阶段2] 合并处理")
    merged_data = merge_hosts(hosts_files)

    # 阶段3: 生成最终文件
    output_path = os.path.join(RULE_DIR, "hosts.txt")
    ensure_directory(output_path)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# 最后更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# 规则总数: {len(merged_data)}\n")
        f.write("# 项目地址: https://github.com/045200/hyper_hosts\n\n")
        for domain, ip in sorted(merged_data.items()):
            f.write(f"{ip}\t{domain}\n")

    print(f"\n=== hosts同步完成 ===")
    print(f"生成文件: {output_path}")
    print(f"规则总数: {len(merged_data)}")

    # 阶段4: 白名单处理
    print("\n[阶段4] 白名单下载与合并")
    whitelist_files = download_white_list()
    if not whitelist_files:
        print("警告: 未下载到任何白名单文件")
    else:
        comment_lines, merged_whitelist = merge_white_list(whitelist_files)
        writelist_path = os.path.join(RULE_DIR, "writelist.txt")
        ensure_directory(writelist_path)
        with open(writelist_path, 'w', encoding='utf-8') as f:
            f.write(f"# 最后更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 白名单总数: {len(merged_whitelist)}\n")
            for line in comment_lines:
                f.write(line + '\n')
            for domain in sorted(merged_whitelist):
                f.write(f"{domain}\n")
        print(f"[白名单生成完成] {writelist_path} (总数: {len(merged_whitelist)})")

if __name__ == "__main__":
    main()