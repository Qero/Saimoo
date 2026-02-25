#!/bin/bash

# 获取脚本所在目录的上一级目录 (项目根目录)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 设置 PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"

# 设置 Streamlit 默认端口，如果环境变量未设置
PORT=${PORT:-8501}

echo "Starting Saimoo UI on port $PORT..."
echo "Project Root: $PROJECT_ROOT"

# 使用 uv 运行 streamlit
# 确保在项目根目录下运行，以便正确加载 .env 和其他配置
cd "$PROJECT_ROOT"

# 如果使用了 uv 管理环境，推荐使用 uv run
if command -v uv &> /dev/null; then
    uv run streamlit run src/saimoo/web/app.py --server.port "$PORT"
else
    # Fallback to python/streamlit if uv is not available (though project uses uv)
    streamlit run src/saimoo/web/app.py --server.port "$PORT"
fi
