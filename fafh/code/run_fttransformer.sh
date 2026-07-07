#!/bin/bash
# 自动运行 predict_fttransformer_advanced.py 的脚本

cd /usr/fafh

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 错误: 虚拟环境不存在"
    exit 1
fi

# 检查虚拟环境的Python是否存在
if [ ! -f "venv/bin/python" ]; then
    echo "❌ 错误: 虚拟环境的Python不存在"
    exit 1
fi

# 显示使用的Python路径
PYTHON_PATH=$(readlink -f venv/bin/python)
echo "🚀 使用Python: $PYTHON_PATH"
echo ""

# 使用虚拟环境的Python运行脚本
venv/bin/python predict_fttransformer_advanced.py "$@"
