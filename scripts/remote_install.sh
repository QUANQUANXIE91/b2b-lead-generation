#!/bin/bash
# ============================================================
# B2B Lead Generation - 一键安装脚本
# ============================================================
# 用法：
#   curl -fsSL https://your-domain.com/install.sh | bash
#   或
#   bash install.sh
# ============================================================

set -e

echo "============================================================"
echo "B2B Lead Generation - 一键安装"
echo "============================================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检测系统
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    SYSTEM="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    SYSTEM="macos"
else
    echo -e "${RED}[ERROR] 不支持的系统: $OSTYPE${NC}"
    exit 1
fi

echo -e "${GREEN}[OK]${NC} 检测到系统: $SYSTEM"

# 检测 Python
PYTHON="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON="python"
fi

if ! command -v $PYTHON &> /dev/null; then
    echo -e "${RED}[ERROR] 未找到 Python，请先安装 Python 3${NC}"
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Python: $($PYTHON --version)"

# 检测 Hermes
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
if [[ ! -d "$HERMES_HOME" ]]; then
    echo -e "${RED}[ERROR] 未找到 Hermes，请先安装 Hermes Agent${NC}"
    echo "       安装命令: curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash"
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Hermes Home: $HERMES_HOME"

# 创建技能目录
SKILL_DIR="$HERMES_HOME/skills/b2b-lead-generation"
mkdir -p "$SKILL_DIR"

echo ""
echo "============================================================"
echo "正在安装 B2B Lead Generation..."
echo "============================================================"
echo ""

# 检测安装方式
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -f "$SCRIPT_DIR/SKILL.md" ]]; then
    # 从本地目录安装
    echo -e "${GREEN}[INFO]${NC} 从本地目录安装..."
    cp -r "$SCRIPT_DIR"/* "$SKILL_DIR/"
else
    # 从压缩包安装
    TAR_FILE="$SCRIPT_DIR/b2b-lead-generation.tar.gz"
    if [[ -f "$TAR_FILE" ]]; then
        echo -e "${GREEN}[INFO]${NC} 从压缩包安装..."
        tar -xzf "$TAR_FILE" -C "$HERMES_HOME/skills/"
    else
        # 从当前脚本目录的父目录安装（假设脚本在技能目录内）
        PARENT_DIR="$(dirname "$SCRIPT_DIR")"
        if [[ -f "$PARENT_DIR/SKILL.md" ]]; then
            echo -e "${GREEN}[INFO]${NC} 从父目录安装..."
            cp -r "$PARENT_DIR"/* "$SKILL_DIR/"
        else
            echo -e "${RED}[ERROR]${NC} 无法找到技能文件"
            exit 1
        fi
    fi
fi

echo -e "${GREEN}[OK]${NC} 文件已复制到: $SKILL_DIR"

# 安装 CLI 命令
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"

WRAPPER="$BIN_DIR/b2b-lead"

cat > "$WRAPPER" << 'WRAPPER_EOF'
#!/bin/bash
# B2B Lead Generation CLI Wrapper
SKILL_DIR="$HOME/.hermes/skills/b2b-lead-generation"
exec python3 "$SKILL_DIR/scripts/cli.py" "$@"
WRAPPER_EOF

chmod +x "$WRAPPER"

echo -e "${GREEN}[OK]${NC} CLI 命令已安装: $WRAPPER"

# 检查 PATH
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo ""
    echo -e "${YELLOW}[WARN]${NC} $BIN_DIR 不在 PATH 中"
    echo "       请将以下内容添加到 ~/.bashrc 或 ~/.zshrc:"
    echo ""
    echo "       export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
    echo "       然后运行: source ~/.bashrc"
    echo ""
fi

# 验证安装
echo ""
echo "============================================================"
echo -e "${GREEN}安装成功！${NC}"
echo "============================================================"
echo ""
echo "快速开始:"
echo "  1. 创建配置: cp $SKILL_DIR/config.example.yaml ~/my-product.yaml"
echo "  2. 编辑配置:   nano ~/my-product.yaml"
echo "  3. 运行搜索:   b2b-lead search --config ~/my-product.yaml"
echo ""
echo "预置模板:"
echo "  - 8 大行业关键词模板: $SKILL_DIR/templates/keywords.yaml"
echo "  - 10 大市场区域模板: $SKILL_DIR/templates/markets.yaml"
echo ""
echo "文档:"
echo "  - 快速上手: $SKILL_DIR/references/quick-start.md"
echo "  - 主文档:   $SKILL_DIR/SKILL.md"
echo ""
