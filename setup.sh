#!/bin/bash

# Linux Shell脚本，用于创建虚拟环境、安装依赖并激活虚拟环境

echo "正在检查Python版本..."
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "错误：未找到Python，请先安装Python"
    exit 1
fi

PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
fi

echo "使用Python命令: $PYTHON_CMD"

echo "正在检查是否已安装venv模块..."
if ! $PYTHON_CMD -c "import venv" &> /dev/null; then
    echo "错误：未找到venv模块，请确保Python安装完整"
    exit 1
fi

echo "正在创建虚拟环境..."
if [ -d "venv" ]; then
    echo "虚拟环境已存在，跳过创建步骤"
else
    $PYTHON_CMD -m venv venv
    if [ $? -ne 0 ]; then
        echo "错误：无法创建虚拟环境"
        exit 1
    fi
    echo "虚拟环境创建成功"
fi

echo "正在激活虚拟环境..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "错误：无法激活虚拟环境"
    exit 1
fi

echo "正在升级pip..."
python -m pip install --upgrade pip > /dev/null 2>&1

echo "正在安装依赖..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "错误：无法安装依赖"
    exit 1
fi

echo ""
echo "虚拟环境已准备就绪！"
echo "要重新激活此虚拟环境，请运行: source venv/bin/activate"
echo "要退出虚拟环境，请运行: deactivate"
echo ""

exec $SHELL