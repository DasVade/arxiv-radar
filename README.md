# arXiv Weekly Radar

## Windows Setup

```powershell
cd C:\MyReserach\arXive_radar
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install arxiv pandas requests pypdf
```

If activation is blocked:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\venv\Scripts\Activate.ps1
```

## Run

```powershell
python arxiv_weekly_radar.py
```

## OpenAI 中文摘要配置

为避免泄露，**不要把 API Key 写在脚本里**。

脚本会按以下顺序读取 Key：
1. `OPENAI_API_KEY` 环境变量
2. `OPENAI_API_KEY_FILE` 指向的文件
3. 默认文件（仓库外）：
   - Windows: `%APPDATA%\arxiv-radar\openai_api_key.txt`
   - 其他系统: `~/.arxiv_radar/openai_api_key.txt`

你使用 Windows 任务计划程序自动跑时，推荐默认文件方式（无需改命令行）：

1. 创建目录：`%APPDATA%\arxiv-radar`
2. 创建文件：`%APPDATA%\arxiv-radar\openai_api_key.txt`
3. 文件内容只放一行你的 OpenAI API Key
4. 正常执行 `python arxiv_weekly_radar.py`


### 使用系统环境变量（推荐，避免密钥落盘）

可以，当前代码已经优先读取 `OPENAI_API_KEY`，所以你可以在命令行一次性写入系统/用户环境变量，任务计划程序后续直接可用（无需改任务命令）。

**Windows（当前用户）**
```powershell
setx OPENAI_API_KEY "你的OpenAI_API_Key"
```

**Windows（系统级，管理员 PowerShell）**
```powershell
setx OPENAI_API_KEY "你的OpenAI_API_Key" /M
```

设置完成后，重启任务计划程序对应进程（或重启机器）以确保新环境变量生效。

脚本会在每篇论文条目下新增：
- 中文摘要（约 80~120 字）
- 中文文章概述（最多 3 个要点）


> 中文概述会优先基于 PDF 正文内容生成（脚本会先尝试读取 arXiv PDF 前几页正文，失败时回退到摘要）。
