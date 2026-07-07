#!/bin/bash
# 运行脚本：自动激活虚拟环境并运行Python脚本

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "❌ 错误: 虚拟环境不存在"
    echo "请先创建虚拟环境:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# 激活虚拟环境并运行脚本
if [ $# -eq 0 ]; then
    echo "使用方法: ./run.sh <python_script.py>"
    echo ""
    echo "示例:"
    echo "  ./run.sh predict_fttransformer_advanced.py"
    echo "  ./run.sh run_complete_analysis.py"
    exit 1
fi

echo "🚀 激活虚拟环境并运行: $1"
echo ""

# 使用虚拟环境的Python运行脚本
venv/bin/python "$@"
