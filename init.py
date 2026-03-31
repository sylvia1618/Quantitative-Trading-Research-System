#!/usr/bin/env python
"""
项目初始化脚本：创建必要的目录和配置文件
"""

import os
import sys
from pathlib import Path


def create_directories():
    """创建必要的目录"""
    directories = [
        "data/raw",
        "data/processed",
        "data/metadata",
        "research/alpha_discovery",
        "research/EDA",
        "logs",
        "models/saved",
        "tmp"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ 创建目录: {directory}")


def create_env_file():
    """创建 .env 文件"""
    env_template = """# Tushare API Token
TUSHARE_TOKEN=your_token_here

# 应用配置
DEBUG=False
LOG_LEVEL=INFO
"""
    
    env_path = ".env"
    if not os.path.exists(env_path):
        with open(env_path, "w") as f:
            f.write(env_template)
        print(f"✅ 创建文件: {env_path}")
    else:
        print(f"⚠️  文件已存在: {env_path}")


def create_gitkeep_files():
    """在空目录中创建 .gitkeep 文件"""
    directories = [
        "data/raw",
        "data/processed",
        "data/metadata",
        "logs",
        "models/saved",
        "tmp"
    ]
    
    for directory in directories:
        gitkeep_path = Path(directory) / ".gitkeep"
        gitkeep_path.touch()
        print(f"✅ 创建 .gitkeep: {directory}/.gitkeep")


def main():
    """主初始化函数"""
    print("🚀 QuantFlow Lab 项目初始化\n")
    
    try:
        create_directories()
        print()
        create_env_file()
        print()
        create_gitkeep_files()
        print()
        print("✨ 初始化完成！\n")
        print("📝 接下来的步骤:")
        print("1. 编辑 config.yaml，填入 API Token")
        print("2. 编辑 .env，配置环境变量")
        print("3. 运行 'pip install -r requirements.txt' 安装依赖")
        print("4. 运行 'streamlit run app/main.py' 启动应用")
    
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
