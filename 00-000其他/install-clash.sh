#!/bin/bash

# 获取clash最新版本号
LATEST_VERSION=$(curl -s https://api.github.com/repos/MetaCubeX/mihomo/releases/latest | grep "tag_name" | cut -d '"' -f 4)

# 生成下载链接
DOWNLOAD_URL="https://github.com/MetaCubeX/mihomo/releases/download/${LATEST_VERSION}/mihomo-linux-amd64-compatible-${LATEST_VERSION}.gz"

echo "开始下载 Clash mihomo ${LATEST_VERSION}..."
wget ${DOWNLOAD_URL}
echo "Clash mihomo下载完成"

echo "开始解压"
gunzip "mihomo-linux-amd64-compatible-${LATEST_VERSION}.gz"
echo "解压完成"

echo "开始重命名"
mv "mihomo-linux-amd64-compatible-${LATEST_VERSION}" clash
echo "重命名完成"

echo "开始添加执行权限"
chmod u+x clash
echo "执行权限添加完成"

echo "开始创建 /etc/clash 目录"
sudo mkdir -p /etc/clash
echo "/etc/clash 目录创建完成"

echo "开始复制 clash 到 /usr/local/bin"
sudo cp clash /usr/local/bin
echo "复制完成"

echo "开始安装docker"
apt install docker.io -y
echo "docker安装完成"

echo "开始安装ui界面"
docker run -d --restart always -p 80:80 --name metacubexd ghcr.io/metacubex/metacubexd
echo "ui界面安装完成"

echo "开始设置 转发"
echo 'net.ipv4.ip_forward = 1' | sudo tee -a /etc/sysctl.conf
echo 'net.ipv6.conf.all.forwarding = 1' | sudo tee -a /etc/sysctl.conf
echo "转发设置完成"

echo "开始创建 systemd 服务"

sudo tee /etc/systemd/system/clash.service > /dev/null <<EOF
[Unit]
Description=Clash daemon, A rule-based proxy in Go.
After=network.target

[Service]
Type=simple
Restart=always
ExecStart=/usr/local/bin/clash -d /etc/clash

[Install]
WantedBy=multi-user.target
EOF

echo "systemd 服务创建完成"
