"""
System Pulse — Network System Monitor Dashboard
A web scraping powered system monitoring dashboard using Scrapling.

Features:
- Real-time system resource monitoring (CPU, RAM, Disk, Network)
- Web scraping of GitHub API for trending repos & status
- HTTP endpoint health checks with Scrapling's StealthyFetcher
- Real-time statistics streaming via WebSocket-like polling
"""

import json
import os
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

# Scrapling imports
from scrapling.fetchers import Fetcher, StealthyFetcher, DynamicFetcher

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

# ===== SYSTEM METRICS COLLECTOR =====
class SystemMetrics:
    """Collects system resource metrics."""
    
    @staticmethod
    def get_cpu_info():
        """Get CPU usage and information."""
        try:
            # Get CPU usage from /proc/stat
            with open('/proc/stat') as f:
                line = f.readline()
            parts = line.split()
            if parts[0] == 'cpu':
                user, nice, system, idle = map(int, parts[1:5])
                total = user + nice + system + idle
                usage = ((total - idle) / total) * 100 if total > 0 else 0
                return {
                    'usage_percent': round(usage, 1),
                    'cores': os.cpu_count(),
                    'model': 'Linux x86_64'
                }
        except Exception:
            pass
        return {'usage_percent': 0, 'cores': os.cpu_count(), 'model': 'Unknown'}
    
    @staticmethod
    def get_memory_info():
        """Get memory usage."""
        try:
            with open('/proc/meminfo') as f:
                info = f.read()
            
            mem = {}
            for line in info.split('\n'):
                if line.startswith('MemTotal:'):
                    mem['total_gb'] = round(int(line.split()[1]) / 1024 / 1024, 2)
                elif line.startswith('MemAvailable:'):
                    mem['available_gb'] = round(int(line.split()[1]) / 1024 / 1024, 2)
            
            if 'total_gb' in mem and 'available_gb' in mem:
                mem['used_gb'] = mem['total_gb'] - mem['available_gb']
                mem['usage_percent'] = round((mem['used_gb'] / mem['total_gb']) * 100, 1)
            return mem
        except Exception:
            return {'total_gb': 0, 'used_gb': 0, 'available_gb': 0, 'usage_percent': 0}
    
    @staticmethod
    def get_disk_info():
        """Get disk usage."""
        try:
            stat = os.statvfs('/')
            total = stat.f_blocks * stat.f_frsize / (1024**3)
            free = stat.f_bfree * stat.f_frsize / (1024**3)
            used = total - free
            return {
                'total_gb': round(total, 2),
                'used_gb': round(used, 2),
                'free_gb': round(free, 2),
                'usage_percent': round((used / total) * 100, 1) if total > 0 else 0
            }
        except Exception:
            return {'total_gb': 0, 'used_gb': 0, 'free_gb': 0, 'usage_percent': 0}
    
    @staticmethod
    def get_network_info():
        """Get network interface statistics."""
        try:
            with open('/proc/net/dev') as f:
                lines = f.readlines()[2:]  # Skip headers
            
            interfaces = []
            for line in lines:
                parts = line.split()
                iface = parts[0].strip(':')
                if iface.startswith('lo'):
                    continue
                interfaces.append({
                    'interface': iface,
                    'rx_bytes': int(parts[1]),
                    'tx_bytes': int(parts[9]),
                    'rx_packets': int(parts[2]),
                    'tx_packets': int(parts[10])
                })
            return interfaces
        except Exception:
            return []
    
    @staticmethod
    def get_uptime():
        """Get system uptime."""
        try:
            with open('/proc/uptime') as f:
                seconds = float(f.readline().split()[0])
            days = int(seconds // 86400)
            hours = int((seconds % 86400) // 3600)
            minutes = int((seconds % 3600) // 60)
            return {
                'seconds': round(seconds, 1),
                'formatted': f'{days}d {hours}h {minutes}m'
            }
        except Exception:
            return {'seconds': 0, 'formatted': 'Unknown'}


# ===== WEB SCRAPING SERVICES =====
class WebScrapingService:
    """Uses Scrapling to fetch and parse web data."""
    
    def __init__(self):
        self.fetcher = None
        self._init_fetcher()
    
    def _init_fetcher(self):
        """Initialize the stealthy fetcher."""
        try:
            StealthyFetcher.adaptive = True
            self.fetcher = StealthyFetcher(delay_before_return=0.5, network_idle=True)
        except Exception:
            self.fetcher = None
    
    @staticmethod
    def get_github_trending(language='python', since='daily'):
        """Scrape GitHub trending repositories using Fetcher.get()."""
        try:
            fetcher = Fetcher()
            url = f'https://github.com/trending/{language}?since={since}'
            response = fetcher.get(url)
            
            # Parse trending repos - new GitHub HTML structure
            repos = []
            articles = response.css('article.Box-row')
            
            for article in articles[:10]:
                # Repo name from href attribute
                href = article.css('h2 a::attr(href)').get('').strip()
                if not href:
                    continue
                
                # Stars: find span with "X stars today" using xpath
                stars_spans = article.css('span')
                stars_today = ''
                for s in stars_spans:
                    texts = s.xpath('.//text()').getall()
                    for txt in texts:
                        txt = txt.strip()
                        if 'stars today' in txt or 'stars this' in txt:
                            stars_today = txt
                            break
                        if 'stars' in txt and txt:
                            stars_today = txt
                            break
                    if stars_today:
                        break
                
                # Extract display name - org/repo from href
                display_name = href.strip('/').replace('/', '/')
                
                repos.append({
                    'name': href.strip('/'),
                    'display_name': display_name,
                    'stars': stars_today if stars_today else 'N/A',
                    'url': f'https://github.com{href}'
                })
            
            return {'source': 'scrapling_fetcher', 'repos': repos}
        
        except Exception as e:
            print(f'Scrapling error: {e}')
            return WebScrapingService._fallback_trending()
    
    @staticmethod
    def get_hacker_news_top():
        """Get top stories from Hacker News."""
        try:
            fetcher = Fetcher()
            response = fetcher.get('https://hacker-news.firebaseio.com/v0/topstories.json')
            story_ids = response.json()[:20]
            
            stories = []
            for sid in story_ids:
                story_resp = fetcher.get(f'https://hacker-news.firebaseio.com/v0/item/{sid}.json')
                story = story_resp.json()
                if story and 'title' in story:
                    stories.append({
                        'title': story.get('title', ''),
                        'url': story.get('url', ''),
                        'points': story.get('points', 0),
                        'comments': story.get('descendants', 0),
                        'author': story.get('by', '')
                    })
            
            return {'source': 'hn_api', 'stories': stories[:20]}
        
        except Exception as e:
            print(f'Hacker News error: {e}')
            return {'source': 'hn_fallback', 'stories': []}
    
    @staticmethod
    def get_reddit_top(subreddit='programming', sort='hot', limit=25):
        """Get top posts from Reddit."""
        try:
            fetcher = Fetcher()
            url = f'https://www.reddit.com/r/{subreddit}/{sort}.json?limit={limit}'
            response = fetcher.get(url, headers={
                'User-Agent': 'SystemPulse/1.0'
            })
            
            data = response.json()
            posts = []
            for post in data.get('data', {}).get('children', []):
                pd = post.get('data', {})
                posts.append({
                    'title': pd.get('title', ''),
                    'url': f'https://reddit.com{pd.get("url", "")}',
                    'score': pd.get('score', 0),
                    'comments': pd.get('num_comments', 0),
                    'author': pd.get('author', ''),
                    'subreddit': pd.get('subreddit', '')
                })
            
            return {'source': 'reddit_api', 'posts': posts}
        
        except Exception as e:
            print(f'Reddit error: {e}')
            return {'source': 'reddit_fallback', 'posts': []}
    
    @staticmethod
    def search_youtube(query, max_results=10):
        """Search YouTube videos."""
        try:
            fetcher = Fetcher()
            url = f'https://www.youtube.com/results?search_query={query.replace(" ", "+")}'
            response = fetcher.get(url)
            
            videos = []
            # Extract video IDs and titles from the page
            video_pattern = r'"/watch\?v=([^&]+)"[^>]*>.*?<span[^>]*>([^<]+)</span>'
            matches = re.findall(video_pattern, response.text, re.DOTALL)
            
            for video_id, title in matches[:max_results]:
                videos.append({
                    'title': title.strip(),
                    'url': f'https://www.youtube.com/watch?v={video_id}',
                    'video_id': video_id
                })
            
            return {'source': 'youtube_search', 'videos': videos}
        
        except Exception as e:
            print(f'YouTube error: {e}')
            return {'source': 'youtube_fallback', 'videos': []}
    
    @staticmethod
    def get_github_trending(language='python', since='daily'):
        """Fallback for trending repos."""
        return {
            'source': 'api_fallback',
            'repos': [
                {'name': 'anthropics/claude-code', 'stars': '⭐ 50k+', 'url': 'https://github.com/anthropics/claude-code'},
                {'name': 'vercel/next.js', 'stars': '⭐ 120k+', 'url': 'https://github.com/vercel/next.js'},
                {'name': 'microsoft/vscode', 'stars': '⭐ 160k+', 'url': 'https://github.com/microsoft/vscode'},
            ]
        }
    
    def check_endpoint_health(self, url, method='GET'):
        """Check health of an HTTP endpoint using Fetcher."""
        try:
            start = time.time()
            fetcher = Fetcher()
            response = fetcher.get(url)
            latency = (time.time() - start) * 1000
            status_code = response.status if hasattr(response, 'status') else getattr(response, 'status_code', 0)
            return {
                'url': url,
                'status': 'healthy' if status_code == 200 else 'unhealthy',
                'status_code': status_code,
                'latency_ms': round(latency, 1),
                'title': self._extract_title(response.text)
            }
        except Exception:
            return {
                'url': url,
                'status': 'error',
                'status_code': 0,
                'latency_ms': 0
            }
    
    def _extract_title(self, html):
        """Extract title from HTML."""
        match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip()[:100] if match else None


# ===== INSTANCES =====
metrics = SystemMetrics()
scraper = WebScrapingService()


# ===== API ROUTES =====
@app.route('/api/system')
def api_system():
    """Get comprehensive system metrics."""
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'cpu': metrics.get_cpu_info(),
        'memory': metrics.get_memory_info(),
        'disk': metrics.get_disk_info(),
        'network': metrics.get_network_info(),
        'uptime': metrics.get_uptime()
    })


@app.route('/api/trending')
def api_trending():
    """Get trending GitHub repos."""
    language = request.args.get('language', 'python')
    since = request.args.get('since', 'daily')
    result = scraper.get_github_trending(language, since)
    return jsonify(result)


@app.route('/api/health')
def api_health():
    """Check health of monitored endpoints."""
    endpoints = [
        'https://github.com',
        'https://api.github.com',
        'https://www.google.com',
    ]
    results = [scraper.check_endpoint_health(url) for url in endpoints]
    return jsonify({'endpoints': results})


@app.route('/api/scrape/<path:url>')
def api_scrape(url):
    """Scrape any URL and return parsed data."""
    try:
        fetcher = Fetcher()
        response = fetcher.get(url)
        status_code = response.status if hasattr(response, 'status') else getattr(response, 'status_code', 0)
        return jsonify({
            'status_code': status_code,
            'url': response.url,
            'title': scraper._extract_title(response.text),
            'content_length': len(response.text),
            'html_preview': response.text[:2000]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/hackernews')
def api_hackernews():
    """Get top Hacker News stories."""
    result = WebScrapingService.get_hacker_news_top()
    return jsonify(result)


@app.route('/api/reddit')
def api_reddit():
    """Get top Reddit posts."""
    subreddit = request.args.get('subreddit', 'programming')
    sort = request.args.get('sort', 'hot')
    limit = request.args.get('limit', 25, type=int)
    result = WebScrapingService.get_reddit_top(subreddit, sort, limit)
    return jsonify(result)


@app.route('/api/youtube')
def api_youtube():
    """Search YouTube videos."""
    query = request.args.get('q', '')
    max_results = request.args.get('limit', 10, type=int)
    if not query:
        return jsonify({'error': 'Query parameter q is required'}), 400
    result = WebScrapingService.search_youtube(query, max_results)
    return jsonify(result)


# ===== WEB DASHBOARD =====
@app.route('/')
def dashboard():
    return render_template('dashboard.html')


if __name__ == '__main__':
    print('🚀 Starting System Pulse Dashboard...')
    print('📊 Dashboard: http://localhost:5000')
    app.run(host='0.0.0.0', port=5000, debug=True)
