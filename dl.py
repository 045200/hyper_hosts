import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import chardet

# 配置参数
MAX_RETRIES = 3
REQUEST_TIMEOUT = 20
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, text like Gecko) Chrome/122.0.0.0 Safari/537.36 GitHubHostsMerger/1.0"

# 带重试机制的Session配置
def create_session():
    session = requests.Session()
    retries = Retry(
        total=MAX_RETRIES,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=frozenset(['GET'])
    )
    session.mount('https://', HTTPAdapter(max_retries=retries))
    session.mount('http://', HTTPAdapter(max_retries=retries))
    return session

def detect_encoding(content):
    # 使用双重检测机制提高准确率
    try:
        result = chardet.detect(content)
        if result['confidence'] > 0.7:
            return result['encoding']
        return 'utf-8'
    except Exception:
        return 'utf-8'

def fetch_and_merge_hosts():
    urls = [
        "https://raw.githubusercontent.com/jdlingyu/ad-wars/master/hosts",
        "https://lingeringsound.github.io/10007_auto/reward",
        "https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/Filters/AWAvenue-Ads-Rule-hosts.txt",
"https://raw.githubusercontent.com/ineo6/hosts/refs/heads/master/hosts"
    ]

    unique_entries = []
    seen = set()
    session = create_session()
    
    start_time = time.time()
    success_count = 0

    for idx, url in enumerate(urls, 1):
        try:
            print(f"🔍 正在处理源({idx}/{len(urls)})：{url}")
            response = session.get(
                url,
                timeout=REQUEST_TIMEOUT,
                headers={'User-Agent': USER_AGENT},
                verify=True  # 保持SSL验证
            )
            response.raise_for_status()
            
            # 智能编码检测
            detected_encoding = detect_encoding(response.content)
            try:
                content = response.content.decode(detected_encoding)
            except UnicodeDecodeError:
                content = response.content.decode('utf-8', errors='replace')

            line_count = 0
            for raw_line in content.splitlines():
                line = raw_line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # 规范化条目（可选扩展点）
                clean_line = line.split('#')[0].strip()  # 去除行内注释
                if clean_line and clean_line not in seen:
                    seen.add(clean_line)
                    unique_entries.append(clean_line)
                    line_count += 1

            success_count += 1
            print(f"✅ 成功获取：{url} | 新增条目：{line_count} | 当前总数：{len(unique_entries)}")
            
        except Exception as e:
            err_msg = f"❌ 源处理失败：{url} | 错误类型：{type(e).__name__}"
            if hasattr(e, 'response'):
                err_msg += f" | 状态码：{e.response.status_code}"
            print(err_msg)
            continue

    # 写入优化
    if unique_entries:
        with open("hosts.txt", "w", encoding="utf-8", newline='\n') as f:
            f.write(f"# Generated by GitHub Actions at {time.strftime('%Y-%m-%d %H:%M:%S UTC%z')}\n")
            f.write("\n".join(unique_entries))
        
        elapsed = time.time() - start_time
        stats = f"""
        ╔═══════════════════════════════╗
        ║         合并完成报告          ║
        ╠═══════════════╦═══════════════╣
        ║ 成功源        ║ {success_count}/{len(urls)}       ║
        ║ 总条目数      ║ {len(unique_entries):<13} ║
        ║ 耗时          ║ {elapsed:.2f}s       ║
        ╚═══════════════╩═══════════════╝
        """
        print(stats)
    else:
        print("⚠️ 警告：未获取到任何有效条目")

if __name__ == "__main__":
    fetch_and_merge_hosts()
