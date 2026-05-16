# 🔥 System Pulse — Web Scraping Dashboard

> **Python Web Scraping 儀表板** — 使用 Scrapling 框架實作的多來源資料爬取系統

## ✨ 功能特色

- 🕷️ **多來源爬蟲** — GitHub Trending, Hacker News, Reddit, YouTube
- 📊 **系統監控** — CPU, 記憶體, 磁碟, 網路即時監控
- 🏥 **健康檢查** — HTTP 服務健康狀態檢測
- ⚡ **高效能** — 基於 Scrapling 的非同步爬蟲架構
- 🎨 **現代化 UI** — 深色主題儀表板介面

## 🚀 快速開始

```bash
# 安裝相依套件
uv pip install flask flask-cors scrapling playwright patchright curl_cffi

# 安裝 Playwright 瀏覽器
uv run playwright install chromium

# 啟動儀表板
uv run python3 app.py
```

## 📁 專案結構

```
creative-project-21/
├── app.py                    # Flask 主程式 (REST API)
├── scraping_app.py           # 獨立爬蟲 Demo
├── index.html                # Landing Page
├── templates/
│   └── dashboard.html        # 儀表板前端
├── .venv/                    # Python 虛擬環境
└── README.md
```

## 📡 API Endpoints

| Endpoint | Method | 說明 |
|----------|--------|------|
| `/api/system` | GET | 系統資源監控 |
| `/api/health` | GET | 服務健康檢查 |
| `/api/trending` | GET | GitHub Trending |
| `/api/hackernews` | GET | Hacker News 熱門 |
| `/api/reddit` | GET | Reddit 熱門 |
| `/api/youtube` | GET | YouTube 搜尋 |

## 🛠️ 技術棧

- **後端**: Python 3.12 + Flask
- **爬蟲**: Scrapling (Fetcher, Spider, StealthyFetcher)
- **瀏覽器**: Playwright + Patchright
- **HTTP**: curl_cffi
- **前端**: HTML/CSS/JS (Vanilla)

## 📊 技術規格

- Scrapling 0.4.8
- Playwright 1.59.0
- Patchright 1.59.1
- curl_cffi 0.15.0
- Flask 3.1.3

## 🔗 官方資源

- [Scrapling GitHub](https://github.com/D4Vinci/Scrapling)
- [Scrapling 文件](https://scrapling.readthedocs.io)
- [GitHub Pages](https://mavisy75106.github.io/creative-project-21/)

## 📄 License

MIT License
