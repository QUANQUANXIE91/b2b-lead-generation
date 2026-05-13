#!/bin/bash
# ============================================================
# B2B Lead Generation - CLI 安装脚本
# ============================================================

set -e

echo "============================================================"
echo "B2B Lead Generation - CLI Installer"
echo "============================================================"
echo ""

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# 检测 Python
PYTHON="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON="python"
fi

# 创建 bin 目录
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"

# 创建 wrapper 脚本
WRAPPER="$BIN_DIR/b2b-lead"

cat > "$WRAPPER" << EOF
#!/bin/bash
# B2B Lead Generation CLI Wrapper
SKILL_DIR="$SKILL_DIR"
exec $PYTHON "\$SKILL_DIR/scripts/cli.py" "\$@"
EOF

chmod +x "$WRAPPER"

echo "[OK] Installed: $WRAPPER"
echo ""

# 检查 PATH
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo "[WARN] $BIN_DIR is not in PATH"
    echo "       Add this line to your ~/.bashrc or ~/.zshrc:"
    echo ""
    echo "       export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
    echo "       Then run: source ~/.bashrc"
fi

# 验证安装
echo "[TEST] Running: b2b-lead --help"
echo ""
$WRAPPER --help

echo ""
echo "============================================================"
echo "[OK] Installation complete!"
echo "============================================================"
echo ""
echo "Quick Start:"
echo "  1. Create config: cp $SKILL_DIR/config.example.yaml my-product.yaml"
echo "  2. Edit config:   nano my-product.yaml"
echo "  3. Run search:    b2b-lead search --config my-product.yaml"
echo ""
