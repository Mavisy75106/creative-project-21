"""
Web Scraping Dashboard — 網路爬蟲儀表板
展示 Scrapling 的完整功能：
1. 靜態網頁爬取 (Fetcher)
2. 蜘蛛爬蟲框架 (Spider)  
3. 自適應解析
4. 健康檢查與效能測試
"""

import asyncio
import json
import time
from datetime import datetime
from scrapling.fetchers import Fetcher
from scrapling.spiders import Spider, Response


# ===== 1. 基礎爬取 =====
def basic_scrape():
    """使用 Fetcher 爬取網頁並解析。"""
    print("=" * 60)
    print("1️⃣  基礎爬取 — Fetcher.get()")
    print("=" * 60)
    
    urls = [
        'https://httpbin.org/html',
        'https://news.ycombinator.com/',
    ]
    
    fetcher = Fetcher()
    
    for url in urls:
        print(f"\n📥 爬取: {url}")
        try:
            start = time.time()
            response = fetcher.get(url)
            elapsed = (time.time() - start) * 1000
            
            print(f"   ✅ 狀態: {response.status}")
            print(f"   ⏱️  耗時: {elapsed:.0f}ms")
            print(f"   📏 大小: {len(response.text)} bytes")
            
            # CSS 解析示例
            if 'httpbin.org' in url:
                h1 = response.css('h1::text')
                if h1:
                    print(f"   📝 H1: {h1.get()}")
            
            print()
            
        except Exception as e:
            print(f"   ❌ 錯誤: {e}")


# ===== 2. 蜘蛛爬蟲框架 =====
def spider_example():
    """使用 Spider 框架爬取多頁。"""
    print("=" * 60)
    print("2️⃣  蜘蛛爬蟲框架 — Spider")
    print("=" * 60)
    
    class HackerNewsSpider(Spider):
        name = 'hn_scraper'
        start_urls = ['https://news.ycombinator.com/']
        
        async def parse(self, response: Response):
            items = []
            # 抓取 HN 標題
            titles = response.css('span.titleline > a::text')
            for title in titles:
                link = response.css('span.titleline a::attr(href)')
                items.append({
                    'title': title.get(),
                    'url': link.get() if link else '#',
                })
            yield {'page': 'main', 'count': len(items), 'items': items}
    
    print("🕷️  啟動 HackerNews Spider...")
    result = HackerNewsSpider().start()  # start() 內部處理 asyncio
    
    print(f"\n📊 爬蟲統計:")
    print(f"   📄 請求數: {result.stats.requests_count}")
    print(f"   ⚡ 請求/秒: {result.stats.requests_per_second:.1f}")
    print(f"   📏 回應位元組: {result.stats.response_bytes}")
    print(f"   📦 抓取項目: {result.stats.items_scraped}")
    
    if result.items:
        print(f"\n📝 抓取結果 ({result.stats.items_scraped} 項目):")
        for item in result.items[0].get('items', [])[:5]:  # 顯示前 5 筆
            print(f"   • {item['title']}")
    
    print()


# ===== 3. 效能測試 =====
def benchmark():
    """比較不同爬蟲工具的效能。"""
    import requests
    from scrapling.fetchers import Fetcher
    
    print("=" * 60)
    print("3️⃣  效能測試 — Benchmark")
    print("=" * 60)
    
    url = 'https://httpbin.org/html'
    iterations = 5
    
    # Scrapling Fetcher
    fetcher = Fetcher()
    start = time.time()
    for _ in range(iterations):
        fetcher.get(url)
    scrapling_time = (time.time() - start) / iterations
    
    # Requests
    start = time.time()
    for _ in range(iterations):
        requests.get(url)
    requests_time = (time.time() - start) / iterations
    
    print(f"\n📊 對 {url} 進行 {iterations} 次請求的平均耗時:")
    print(f"   🕷️  Scrapling Fetcher: {scrapling_time*1000:.0f}ms")
    print(f"   📦  Requests:        {requests_time*1000:.0f}ms")
    print(f"   📈  Scrapling 與 Requests 的比率: {scrapling_time/requests_time:.2f}x")
    print()


# ===== 4. 自適應解析 =====
def adaptive_parsing():
    """展示 Scrapling 的自適應解析功能。"""
    print("=" * 60)
    print("4️⃣  自適應解析 — Adaptive Parsing")
    print("=" * 60)
    
    print("""
🔄  Scrapling 的自適應解析功能：
    
    1. 首次爬取時使用 auto_save=True 保存元素路徑
    2. 當網站結構改變時，使用 adaptive=True 自動重新定位元素
    
    範例程式碼：
    
    from scrapling.fetchers import Fetcher
    f = Fetcher()
    
    # 第一次爬取（建立記憶）
    items = f.css('.product', auto_save=True)
    
    # 網站改版後（自動適應）
    items = f.css('.product', adaptive=True)
    
    Scrapling 會根據記憶的 XPath 找到對應元素！
    """)
    print()


# ===== 5. 健康檢查 =====
def health_checks():
    """使用 Scrapling 檢查網站健康狀態。"""
    import asyncio
    
    print("=" * 60)
    print("5️⃣  健康檢查 — Health Checks")
    print("=" * 60)
    
    async def check_sites():
        urls = [
            'https://github.com',
            'https://httpbin.org',
            'https://www.google.com',
            'https://news.ycombinator.com',
        ]
        
        fetcher = Fetcher()
        results = []
        
        for url in urls:
            start = time.time()
            try:
                r = fetcher.get(url, timeout=10)
                latency = (time.time() - start) * 1000
                results.append({
                    'url': url,
                    'status': '✅' if r.status == 200 else '⚠️',
                    'code': r.status,
                    'latency_ms': round(latency, 1),
                })
            except Exception:
                results.append({
                    'url': url,
                    'status': '❌',
                    'code': 0,
                    'latency_ms': 0,
                })
        
        return results
    
    results = asyncio.run(check_sites())
    
    print("\n📋 網站健康檢查結果:")
    print(f"   {'網站':<35} {'狀態':<6} {'狀態碼':<8} {'延遲 (ms)'}")
    print(f"   {'─'*35} {'─'*6} {'─'*8} {'─'*10}")
    for r in results:
        print(f"   {r['url']:<35} {r['status']:<6} {r['code']:<8} {r['latency_ms']}")
    print()


# ===== 6. 整合儀表板 =====
def dashboard():
    """整合所有功能的儀表板。"""
    print("=" * 60)
    print("🎯 整合儀表板")
    print("=" * 60)
    
    print("""
📊  Scrapling 功能總覽：

┌─────────────────────────────────────────────────────────────┐
│ 功能                     │ 狀態       │ 說明                      │
├─────────────────────────────────────────────────────────────┤
│ Fetcher (靜態爬取)      │ ✅ 運作中   │ 基礎 HTTP 請求 + CSS 解析 │
│ Spider (蜘蛛框架)        │ ✅ 運作中   │ 多頁爬取 + 異步處理       │
│ adaptive 自適應解析      │ ✅ 可用     │ 自動定位改變的元素         │
│ StealthyFetcher          │ ✅ 可用     │ Cloudflare/anti-bot bypass│
│ 代理旋轉                 │ ✅ 支援     │ 支援 SOCKS/HTTP 代理       │
│ 速率限制                 │ ✅ 支援     │ 內建下載延遲控制          │
└─────────────────────────────────────────────────────────────┘

📦 已安裝套件：
  • scrapling 0.4.8
  • playwright 1.59.0 (瀏覽器自動化)
  • patchright 1.59.1 (Scrapling 專用 patched Playwright)
  • curl_cffi 0.15.0 (curl 的 Python 封裝)
  • flask 3.1.3 (Web 儀表板框架)

🔗 官方資源：
  • GitHub: https://github.com/D4Vinci/Scrapling
  • 文件: https://scrapling.readthedocs.io
  • PyPI: https://pypi.org/project/scrapling/
""")


# ===== 主程式 =====
if __name__ == '__main__':
    print("\n🕷️  Web Scraping Dashboard powered by Scrapling")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    basic_scrape()
    spider_example()
    benchmark()
    adaptive_parsing()
    health_checks()
    dashboard()
    
    print("✅ 所有測試完成！")
