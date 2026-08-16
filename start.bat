@echo off
chcp 65001 >nul
echo ========================================
echo   PDF 文档问答助手 - 启动脚本
echo ========================================
echo.

REM 检查 Ollama 是否运行
echo [1/3] 检查 Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo Ollama 未运行，正在启动...
    start /min "Ollama" "C:\Users\itlyk\AppData\Local\Programs\Ollama\ollama.exe" serve
    timeout /t 3 >nul
) else (
    echo Ollama 已在运行
)

echo.
echo [2/3] 启动应用...
cd /d "%~dp0"

REM 启动 Streamlit 应用
echo.
echo [3/3] 打开浏览器...
timeout /t 2 >nul
start http://localhost:8501

REM 运行应用
python -m streamlit run app.py --server.port 8501

pause