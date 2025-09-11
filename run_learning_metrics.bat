@echo off
echo 🚀 NL-SQL Agent Learning Metrics
echo ================================
echo.

REM Check if server is running
echo 🔍 Checking if server is running...
curl -s -f "http://localhost:8000/health" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Server is running on port 8000
) else (
    echo ❌ Server is not running on port 8000
    echo Please start the server first with:
    echo   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    echo.
    pause
)

echo.
echo 📊 Available Learning Metrics:
echo   🎨 Dashboard: http://localhost:8000/learning/dashboard
echo   📈 Raw JSON: http://localhost:8000/learning/metrics
echo.

echo 🎯 Choose your view:
echo   1) Beautiful Dashboard (recommended)
echo   2) Raw JSON Metrics
echo   3) Both (open dashboard, show JSON in terminal)
echo.

set /p choice="Enter choice (1-3): "

if "%choice%"=="1" (
    echo 🎨 Opening Learning Dashboard...
    start http://localhost:8000/learning/dashboard
    echo ✅ Dashboard opened in browser!
) else if "%choice%"=="2" (
    echo 📈 Opening Raw Metrics...
    start http://localhost:8000/learning/metrics
    echo ✅ Raw metrics opened in browser!
) else if "%choice%"=="3" (
    echo 🎨 Opening Learning Dashboard...
    start http://localhost:8000/learning/dashboard
    echo ✅ Dashboard opened in browser!
    echo.
    echo 📈 Raw Metrics (also displayed below):
    echo ======================================
    curl -s "http://localhost:8000/learning/metrics"
) else (
    echo ❌ Invalid choice. Opening dashboard by default...
    start http://localhost:8000/learning/dashboard
)

echo.
echo 🎯 Dashboard Features:
echo   📊 Real-time metrics visualization
echo   📈 Query category performance
echo   ⚠️ Error pattern analysis
echo   🔍 Query complexity breakdown
echo   🎯 Accuracy by source (AI/Heuristic/Cache)
echo   🔄 Auto-refresh every 30 seconds
echo.
echo 💡 Pro Tips:
echo   - Run some queries to populate the metrics
echo   - Use the refresh button for manual updates
echo   - Dashboard updates automatically every 30 seconds
echo   - Check the raw JSON for detailed data structure
echo.
echo 🚀 Happy analyzing!
pause
