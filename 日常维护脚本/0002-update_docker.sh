#!/bin/bash

IMAGE_NAME="ghcr.io/metacubex/metacubexd-server"

# 1. 获取当前的镜像 ID（如果不存在则为空）
OLD_ID=$(docker images -q "$IMAGE_NAME:latest")

# 2. 拉取最新镜像
echo "正在检查镜像更新..."
docker pull "$IMAGE_NAME:latest"

# 3. 获取拉取后的新镜像 ID
NEW_ID=$(docker images -q "$IMAGE_NAME:latest")

# 4. 对比镜像 ID
if [ "$OLD_ID" = "$NEW_ID" ] && [ -n "$OLD_ID" ]; then
    echo "【提示】当前已是最新版本，无需重启容器。"
    exit 0
fi

echo "【检测到更新】正在部署新版容器..."

# 5. 执行重启和清理流程
docker stop metacubexd-server || true
docker rm metacubexd-server || true
docker run -d --restart always -p 80:8080 --name metacubexd-server "$IMAGE_NAME"
docker system prune -f

echo "【成功】新版本容器已成功运行！"


创建文件：nano update_meta.sh 并把上面的代码贴进去。

赋予执行权限：chmod +x update_meta.sh

运行：./update_meta.sh
