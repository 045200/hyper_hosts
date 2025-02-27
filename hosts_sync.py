import os
import requests
from requests.exceptions import RequestException

# 配置参数
TEMP_FILE = "/data/python/combined_hosts.tmp"  # 合并后的临时文件
OUTPUT_FILE = "/data/rules/merged_hosts.txt"   # 最终输出文件
HOSTS_URLS = [
    "https://ghproxy.net/raw.githubusercontent.com/jdlingyu/ad-wars/master/hosts",
    "https://raw.gitmirror.com/lingeringsound/10007_auto/master/reward",
    "https://ghfast.top/https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/Filters/AWAvenue-Ads-Rule-hosts.txt"
]
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def ensure_directory(path):
    """确保目录存在"""
    os.makedirs(os.path.dirname(path), exist_ok=True)

def download_combined():
    """将所有订阅内容下载到单个临时文件"""
    try:
        # 清空或创建临时文件
        with open(TEMP_FILE, 'w', encoding='utf-8') as f:
            f.write("")
            
        for index, url in enumerate(HOSTS_URLS, 1):
            try:
                response = requests.get(url, headers=HEADERS, timeout=20)
                response.raise_for_status()
                
                # 自动检测编码
                if response.encoding:
                    content = response.text
                else:
                    content = response.content.decode('utf-8', 'ignore')
                
                # 追加写入临时文件
                with open(TEMP_FILE, 'a', encoding='utf-8') as f:
                    f.write(f"# Source {index}: {url}\n")  # 添加来源标记
                    f.write(content)
                    if not content.endswith('\n'):
                        f.write('\n')  # 确保换行分隔
                print(f"✓ 成功下载 URL#{index}")
                
            except RequestException as e:
                print(f"✗ 下载失败 URL#{index}: {str(e)}")
            except UnicodeDecodeError:
                print(f"⚠ 解码失败 URL#{index}，使用替代解码方案")
                with open(TEMP_FILE, 'a', encoding='utf-8') as f:
                    f.write(response.content.decode('gbk', 'ignore'))
    
    except Exception as e:
        print(f"‼ 严重错误: {str(e)}")

def process_hosts():
    """处理合并后的文件"""
    seen = set()
    processed = []
    
    try:
        with open(TEMP_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.rstrip('\n')
                stripped = line.strip()
                
                # 保留注释和分隔标记
                if stripped.startswith('#') or not stripped:
                    processed.append(line + '\n')
                    continue
                
                # 有效规则处理
                if ' ' in stripped and not stripped.startswith(('!', '@')):
                    rule = stripped.split()[1]  # 提取域名部分
                    if rule not in seen:
                        processed.append(line + '\n')
                        seen.add(rule)
    
    except UnicodeDecodeError:
        print("⚠ 临时文件解码失败，尝试GBK编码重试")
        with open(TEMP_FILE, 'r', encoding='gbk') as f:
            for line in f:
                stripped = line.strip()
                if ' ' in stripped and not stripped.startswith(('!', '@')):
                    rule = stripped.split()[1]
                    if rule not in seen:
                        processed.append(line)
                        seen.add(rule)

    # 写入最终文件
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.writelines([
            "# Merged Hosts\n",
            "# Total unique rules: {}\n".format(len(seen)),
            "# Sources:\n" + ''.join([f"# - {url}\n" for url in HOSTS_URLS]) + "\n"
        ])
        f.writelines(processed)
    print(f"✅ 生成最终文件：{OUTPUT_FILE} (去重后 {len(seen)} 条规则)")

def cleanup():
    """清理临时文件"""
    if os.path.exists(TEMP_FILE):
        os.remove(TEMP_FILE)
        print("♻ 已清理临时文件")

def main():
    ensure_directory(TEMP_FILE)
    ensure_directory(OUTPUT_FILE)
    download_combined()
    process_hosts()
    cleanup()

if __name__ == "__main__":
    main()
