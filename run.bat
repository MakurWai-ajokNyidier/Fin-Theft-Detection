@echo off
:: ╔══════════════════════════════════════════════╗
:: ║  Fin-Theft Detection System — Windows       ║
:: ╚══════════════════════════════════════════════╝
echo.
echo   FIN-THEFT DETECTION SYSTEM v2.1
echo   ─────────────────────────────────
if "%ANTHROPIC_API_KEY%"=="" (
  echo   WARNING: ANTHROPIC_API_KEY not set - demo mode active
  echo   Set it with: set ANTHROPIC_API_KEY=sk-ant-...
) else (
  echo   API key detected OK
)
echo.
pip install -r requirements.txt -q
python app.py
pause
