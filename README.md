# arXiv Weekly Radar

## Windows Setup

```powershell
cd C:\MyReserach\arXive_radar
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install arxiv pandas requests
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
