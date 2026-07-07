#!/bin/bash
# 一键运行脚本 - 最简单的方法

cd /usr/fafh

echo "=========================================="
echo "🚀 运行 predict_fttransformer_advanced.py"
echo "=========================================="
echo ""

# 确保使用虚拟环境的Python
VENV_PYTHON="/usr/fafh/venv/bin/python"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ 错误: 虚拟环境不存在"
    exit 1
fi

echo "✅ 使用Python: $VENV_PYTHON"
echo ""

# 运行脚本
exec "$VENV_PYTHON" predict_fttransformer_advanced.py "$@"
