import requests

# 定义规则源URL列表
urls = [
    "https://ghproxy.net/raw.githubusercontent.com/jdlingyu/ad-wars/master/hosts",
    "https://raw.gitmirror.com/lingeringsound/10007_auto/master/reward",
    "https://ghfast.top/https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/Filters/AWAvenue-Ads-Rule-hosts.txt"
]

def fetch_and_merge_hosts():
    unique_entries = []  # 保留顺序的唯一条目
    seen = set()         # 用于快速查重

    for url in urls:
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()  # 检查HTTP错误

            # 处理编码（优先尝试UTF-8，失败则使用替代方案）
            try:
                content = response.content.decode('utf-8')
            except UnicodeDecodeError:
                content = response.content.decode('latin-1', errors='ignore')

            # 按行处理内容
            for line in content.splitlines():
                stripped = line.strip()
                # 跳过空行和注释
                if stripped and not stripped.startswith('#'):
                    if stripped not in seen:
                        seen.add(stripped)
                        unique_entries.append(stripped)

            print(f"Processed: {url}")

        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch {url}: {str(e)}")
            continue

    # 写入合并后的hosts文件
    if unique_entries:
        with open("hosts.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(unique_entries))
        print(f"Success! Merged {len(unique_entries)} unique entries into hosts.txt")
    else:
        print("No valid host entries found!")

if __name__ == "__main__":
    fetch_and_merge_hosts()
