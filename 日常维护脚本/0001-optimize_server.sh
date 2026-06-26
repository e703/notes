#!/bin/bash

# ======================================================
# 服务器内存优化脚本 - 包含 Swap 创建与系统调优
# 适用于 Ubuntu/Debian/CentOS 7+
# ======================================================

# 颜色定义
RED='\033[31m'
GREEN='\033[32m'
YELLOW='\033[33m'
BLUE='\033[34m'
NC='\033[0m' # 无颜色

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_title() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# 检查是否为 root 用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要 root 权限运行！"
        log_info "请执行: sudo bash $0"
        exit 1
    fi
}

# 检查磁盘空间
check_disk_space() {
    log_info "检查磁盘空间..."
    AVAILABLE=$(df / --output=avail -h | tail -1 | sed 's/G//' | awk '{print int($1)}')
    if [[ $AVAILABLE -lt 4 ]]; then
        log_warn "根目录剩余空间仅 ${AVAILABLE}GB，创建 2GB Swap 可能不够用"
        read -p "是否继续？(y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        log_info "根目录剩余空间: ${AVAILABLE}GB，空间充足 ✅"
    fi
}

# 检查是否已有 Swap
check_existing_swap() {
    log_info "检查现有 Swap..."
    CURRENT_SWAP=$(swapon --show | grep -v "TYPE" | wc -l)
    if [[ $CURRENT_SWAP -gt 0 ]]; then
        log_warn "检测到已存在 Swap 设备："
        swapon --show
        read -p "是否要删除旧的 Swap 并重新创建？(y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "正在关闭并移除旧 Swap..."
            # 从 fstab 中移除旧记录
            sudo sed -i '/swap/d' /etc/fstab
            # 关闭所有 swap
            sudo swapoff -a
            # 删除旧 swapfile（如果存在）
            [[ -f /swapfile ]] && sudo rm -f /swapfile
            log_info "旧 Swap 已移除 ✅"
        else
            log_info "保留现有 Swap，跳过创建步骤"
            return 1
        fi
    fi
    return 0
}

# 创建 Swap 文件
create_swap() {
    log_title "开始创建 2GB Swap 文件"
    
    log_info "步骤 1/4: 创建 2GB 空文件..."
    sudo dd if=/dev/zero of=/swapfile bs=1M count=2048 status=progress
    
    log_info "步骤 2/4: 设置安全权限 (600)..."
    sudo chmod 600 /swapfile
    
    log_info "步骤 3/4: 格式化为 Swap..."
    sudo mkswap /swapfile
    
    log_info "步骤 4/4: 启用 Swap..."
    sudo swapon /swapfile
    
    log_info "Swap 创建并启用成功！✅"
}

# 永久挂载 Swap
make_permanent() {
    log_info "配置开机自动挂载..."
    if grep -q "/swapfile" /etc/fstab; then
        log_warn "/etc/fstab 中已存在 swapfile 条目，跳过"
    else
        echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
        log_info "已写入 /etc/fstab ✅"
    fi
}

# 优化系统参数
optimize_sysctl() {
    log_title "系统参数优化"
    
    # 备份当前 sysctl 配置
    sudo cp /etc/sysctl.conf /etc/sysctl.conf.bak.$(date +%Y%m%d_%H%M%S)
    
    # 定义要添加的优化参数
    cat << 'EOF' | sudo tee -a /etc/sysctl.conf

# ========== 内存优化参数 (添加于 $(date)) ==========
# 控制 Swap 使用倾向：数值越小越倾向使用物理内存 (0-100)
vm.swappiness=10

# 控制缓存回收倾向：数值越大越积极回收 (0-100)
vm.vfs_cache_pressure=50

# 内存耗尽时允许触发 OOM Killer，避免系统卡死
vm.panic_on_oom=0

# 脏页阈值：当脏页达到内存 10% 时开始写回
vm.dirty_ratio=20
vm.dirty_background_ratio=5

# TCP 内存优化
net.core.rmem_max=134217728
net.core.wmem_max=134217728
net.ipv4.tcp_rmem=4096 87380 134217728
net.ipv4.tcp_wmem=4096 65536 134217728

# 文件句柄限制
fs.file-max=1000000
EOF
    
    log_info "优化参数已写入 /etc/sysctl.conf"
    
    # 立即生效
    sudo sysctl -p
    log_info "优化参数已生效 ✅"
}

# 调整文件描述符限制
optimize_limits() {
    log_title "调整系统资源限制"
    
    # 修改 limits.conf
    cat << 'EOF' | sudo tee -a /etc/security/limits.conf

# ========== 资源限制优化 (添加于 $(date)) ==========
* soft nofile 65535
* hard nofile 65535
* soft nproc 65535
* hard nproc 65535
root soft nofile 65535
root hard nofile 65535
EOF
    
    log_info "资源限制已配置 ✅"
}

# 显示优化后的状态
show_status() {
    log_title "优化完成 - 系统状态"
    
    echo ""
    echo "📊 内存使用状态："
    free -h
    
    echo ""
    echo "📊 Swap 详细信息："
    swapon --show
    
    echo ""
    echo "📊 关键内核参数："
    sysctl vm.swappiness vm.vfs_cache_pressure vm.dirty_ratio
    
    echo ""
    echo "📊 磁盘使用情况："
    df -h /
    
    echo ""
    log_info "✅ 所有优化已完成！"
    echo ""
    echo "📝 如需回滚配置："
    echo "   - sysctl: sudo cp /etc/sysctl.conf.bak.* /etc/sysctl.conf && sudo sysctl -p"
    echo "   - limits: 手动编辑 /etc/security/limits.conf 删除添加的部分"
    echo "   - swap:   sudo swapoff /swapfile && sudo rm -f /swapfile && 编辑 /etc/fstab 删除对应行"
}

# 主函数
main() {
    echo ""
    log_title "Linux 服务器一键内存优化脚本"
    echo ""
    
    # 检查权限
    check_root
    
    # 显示开始时间
    START_TIME=$(date '+%Y-%m-%d %H:%M:%S')
    log_info "开始时间: $START_TIME"
    echo ""
    
    # 执行各项任务
    check_disk_space
    echo ""
    
    if check_existing_swap; then
        create_swap
        make_permanent
    else
        log_info "跳过 Swap 创建步骤"
    fi
    
    echo ""
    optimize_sysctl
    
    echo ""
    optimize_limits
    
    echo ""
    show_status
    
    END_TIME=$(date '+%Y-%m-%d %H:%M:%S')
    log_info "结束时间: $END_TIME"
    echo ""
    log_info "🎉 脚本执行完毕！"
}

# 执行主函数
main
