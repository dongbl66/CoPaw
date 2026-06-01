#!/bin/bash
# AI辅助评审系统 Demo - 一键启动 (Linux/macOS)

echo "========================================"
echo "  🤖 AI辅助评审系统 Demo"
echo "========================================"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 需要 Python 3.10+，请先安装"
    exit 1
fi

# 安装依赖
echo "📦 安装依赖..."
pip install -q fastapi uvicorn python-multipart 2>/dev/null

# 清理旧数据
rm -rf demo_data/

# 启动
echo "🚀 启动服务..."
echo ""
echo "  Web UI:  http://localhost:8000"
echo "  API文档: http://localhost:8000/docs"
echo ""
python app.py
