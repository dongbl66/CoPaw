@echo off
REM AI辅助评审系统 Demo - 一键启动 (Windows)

echo ========================================
echo   AI辅助评审系统 Demo
echo ========================================

echo 安装依赖...
pip install -q fastapi uvicorn python-multipart

echo 清理旧数据...
if exist demo_data rmdir /s /q demo_data

echo.
echo 启动服务...
echo   Web UI:  http://localhost:8000
echo   API文档: http://localhost:8000/docs
echo.

python app.py
pause
