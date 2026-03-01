# arXiv Weekly Radar / arXiv 每周雷达

## 1) 用途 / Purpose

### 中文
这个项目会每周从 arXiv（`cs.CV / cs.LG / cs.RO / cs.AI`）抓取近 7 天论文，按关键词兴趣桶筛选并打分，输出：
- 每周精选 Markdown（`weekly_top_picks.md`）
- RIS 引用文件（`weekly_picks.ris`）
- 已读论文 ID（避免重复）

如果配置了 OpenAI API Key，还会为每篇精选论文生成：
- 中文摘要（约 80~120 字）
- 中文文章概述（最多 3 条）

概述优先参考 PDF 正文（前几页文本），PDF 读取失败时回退到摘要。

### English
This project fetches recent arXiv papers (last 7 days) from `cs.CV / cs.LG / cs.RO / cs.AI`, ranks them by keyword buckets, and generates:
- Weekly markdown picks (`weekly_top_picks.md`)
- RIS export (`weekly_picks.ris`)
- Seen paper IDs (to avoid duplicates)

If OpenAI API key is configured, it also adds:
- Chinese summary (about 80–120 Chinese characters)
- Chinese 3-point overview

The overview prefers PDF body text (first pages) and falls back to abstract if PDF extraction fails.

---

## 2) 安装教程 / Installation

### 中文（Windows）
```powershell
cd C:\MyReserach\arXive_radar
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -U arxiv pandas requests pypdf
```

如果 PowerShell 禁止脚本执行：
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\venv\Scripts\Activate.ps1
```

### English (Windows)
```powershell
cd C:\MyReserach\arXive_radar
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -U arxiv pandas requests pypdf
```

If activation is blocked:
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\venv\Scripts\Activate.ps1
```

---

## 3) 使用教程 / Usage

### 中文
运行：
```powershell
python arxiv_weekly_radar.py
```

输出目录默认在：
- `arxiv_radar_weekly/archive/<YYYY-MM-DD>/weekly_top_picks.md`
- `arxiv_radar_weekly/archive/<YYYY-MM-DD>/weekly_picks.ris`

### English
Run:
```powershell
python arxiv_weekly_radar.py
```

Default outputs:
- `arxiv_radar_weekly/archive/<YYYY-MM-DD>/weekly_top_picks.md`
- `arxiv_radar_weekly/archive/<YYYY-MM-DD>/weekly_picks.ris`

---

## 4) OpenAI Key 配置（安全）/ OpenAI Key Setup (Secure)

### 中文
请不要把 API Key 写进代码。脚本会按顺序读取：
1. `OPENAI_API_KEY` 环境变量
2. `OPENAI_API_KEY_FILE` 指向的文件
3. 默认文件（仓库外）：
   - Windows: `%APPDATA%\arxiv-radar\openai_api_key.txt`
   - Others: `~/.arxiv_radar/openai_api_key.txt`

Windows 推荐（不改任务命令）：
1. 创建目录：`%APPDATA%\arxiv-radar`
2. 创建文件：`%APPDATA%\arxiv-radar\openai_api_key.txt`
3. 文件中只保留一行 key

也可以设置环境变量（推荐）：
```powershell
setx OPENAI_API_KEY "你的OpenAI_API_Key"
```
系统级（管理员）：
```powershell
setx OPENAI_API_KEY "你的OpenAI_API_Key" /M
```
设置后重启终端/任务计划程序进程。

### English
Do not hardcode API keys in source files. The script resolves key in this order:
1. `OPENAI_API_KEY`
2. `OPENAI_API_KEY_FILE`
3. Default external file:
   - Windows: `%APPDATA%\arxiv-radar\openai_api_key.txt`
   - Others: `~/.arxiv_radar/openai_api_key.txt`

Windows recommended approach (no task command changes):
1. Create folder `%APPDATA%\arxiv-radar`
2. Create `%APPDATA%\arxiv-radar\openai_api_key.txt`
3. Put one line with your API key

Or set env var:
```powershell
setx OPENAI_API_KEY "your_OpenAI_API_Key"
```
Machine-wide (Admin):
```powershell
setx OPENAI_API_KEY "your_OpenAI_API_Key" /M
```
Restart terminal / Task Scheduler process after setting it.

---

## 5) 怎么更改兴趣内容 / How to Change Your Interests

### 中文
兴趣策略在 `arxiv_weekly_radar.py` 里可配置：

1. **分类范围**（抓哪些 arXiv 类别）
   - `CATEGORIES = ["cs.CV", "cs.LG", "cs.RO", "cs.AI"]`

2. **关键词兴趣桶**（核心）
   - `BUCKETS = {...}`
   - 你可以新增/删除桶，或修改关键词列表

3. **每周挑选数量和比例**
   - `TOTAL_PICKS = 10`
   - `RATIO = (6, 3, 1)`（对应 P1/P2/P3）

4. **过滤阈值**
   - `MIN_HITS_ANY_BUCKET = 2`（命中太少会被过滤）

5. **时间窗口与抓取量**
   - `DAYS_BACK = 7`
   - `MAX_RESULTS = 300`

> 修改后重新运行脚本即可生效。

### English
Interest tuning is configured in `arxiv_weekly_radar.py`:

1. **Category scope**
   - `CATEGORIES = ["cs.CV", "cs.LG", "cs.RO", "cs.AI"]`

2. **Keyword buckets (core relevance logic)**
   - `BUCKETS = {...}`
   - Add/remove buckets or edit keyword lists

3. **Weekly pick count and ratio**
   - `TOTAL_PICKS = 10`
   - `RATIO = (6, 3, 1)` for P1/P2/P3

4. **Filter threshold**
   - `MIN_HITS_ANY_BUCKET = 2`

5. **Time window and fetch size**
   - `DAYS_BACK = 7`
   - `MAX_RESULTS = 300`

> Re-run the script after editing configs.

---

## 6) Windows 任务计划程序建议 / Task Scheduler Tips

### 中文
- Program: `C:\MyReserach\arXive_radar\venv\Scripts\python.exe`
- Arguments: `arxiv_weekly_radar.py`
- Start in: `C:\MyReserach\arXive_radar`

### English
- Program: `C:\MyReserach\arXive_radar\venv\Scripts\python.exe`
- Arguments: `arxiv_weekly_radar.py`
- Start in: `C:\MyReserach\arXive_radar`

---

## 7) 常见问题 / FAQ

### Q1: 会把下载的 PDF 存盘吗？
不会。当前是内存解析 PDF 文本，不会把 PDF 文件写入磁盘。

### Q2: 没配置 OpenAI 会怎样？
脚本会继续执行，只是中文摘要/概述会显示未配置提示。
