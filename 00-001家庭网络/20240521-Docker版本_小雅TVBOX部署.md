# Docker版本——小雅TVBOX部署

## 1.先决条件：

*1.1 ubuntu Server 系统（LXC、VM、Hyper-V、multipass都行）*

*1.2 阿里网盘key，pikpak账户*

## 2.环境部署

### 2.1 Windows本机访问环境部署

下载安装multipass安装，使用默认Hyper-V开启本机虚拟化；

### 2.2 multipass使用

#### 2.2.1查看支持的系统镜像列表

`multipass find`

#### 2.2.2 新建和运行 ubuntu

`multipass launch --name <虚拟机实例名称> <系统镜像名称(可选)>`

举例，比如创建一个名为 vm1 的虚拟机实例，不写系统镜像这个参数，则表示最新版ubuntu 24.04

`multipass launch --name vm1`

以后如何调用虚拟机？

*方法一 任务栏图标点击右键——Open Shell*

*方法二 运行指定虚拟机实例名称即可*

`multipass shell vm1`

#### 2.2.3 如何换 国内 软件源 比如阿里云 Ubuntu 24.04 为例

`sudo sed -i 's|http://archive.ubuntu.com/|http://mirrors.aliyun.com/|g' /etc/apt/sources.list.d/ubuntu.sources`

或者手动修改 配置文件

`nano /etc/apt/sources.list.d/ubuntu.sources`

然后更新软件源

`sudo -i`
`apt update -y`
`apt upgrade -y`

#### 2.2.4 如何删除虚拟机实例（分三步）

##### 停止 vm1
`multipass stop vm1`

##### 删除 vm1
`multipass delete vm1`

##### 清理回收
`multipass purge`

##### 停止全部虚拟机
`multipass stop --all`

#### 2.2.5 查看虚拟机列表

查看虚拟机列表 包括其状态（正在运行、已经删除的、已经停止的、标记未知状态的）

`multipass list`

#### 2.2.6 进阶使用

新建 4核心 4GB内存 300G虚拟磁盘的ubuntu 实例

`multipass launch --name vm3 -c 4 -m 4G -d 300G`

| 参数    | 含义解释                                                     |
| ------- | ------------------------------------------------------------ |
| vm3     | 虚拟机名称                                                   |
| -c 4    | 代表虚拟4核心 这个要根据实际CPU核心数确定 不能随便写 比如本身2核心的cpu是无法虚拟4核心的 |
| -m 4G   | 代表虚拟4GB内存                                              |
| -d 300G | 代表分配虚拟磁盘300GB                                        |

#### 2.3 设置桥接模式的网络

`multipass set local.bridged-network=<name>`

比如重命名以太网2为lan2

`multipass set local.bridged-network=lan2`

<name> 就是网口的名称 比如 以太网，但是最好重命名为英文，比如lan1、lan2



创建桥接模式的虚拟机vm4

`multipass launch --name vm4 -c 4 -m 4G -d 300G --network bridged`



2.2 LXC环境部署
2.3 其他环境部署



安装小雅影音服务器

wget -qO pi.sh https://cafe.cpolar.cn/wkdaily/zero3/raw/branch/main/zero3/pi.sh && chmod +x pi.sh && ./pi.sh






TVBox APK 下载地址 https://wkdaily.cpolar.cn/archives/free
视频里的脚本地址：https://github.com/wukongdaily/OrangePiShell


0 5 * * * apt update && apt -y --auto-remove --purge full-upgrade && apt -y --purge autoremove && apt clean -y
0 6 * * 5 reboot
0 0 * * * find /var/log -name "*.*" -type f -mtime +7 -exec rm -f {} \;



