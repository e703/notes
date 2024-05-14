# easymosdns安装
pve  8.0.4
lxc版本 ubuntu 22.04版本
## lxc系统配置（略）
首先我们来安装一个lxc系统
```
/var/lib/vz/template/cache
```
lxc容器优化 创建完成后不要开机，我们来添加一些配置。进入对应容器的选项 勾选 嵌套   nfs   smb fuse 进入pve控制台，进入/etc/pve/lxc文件夹，修改对应的配置文件，添加以下内容
```
lxc.apparmor.profile: unconfined
lxc.cgroup.devices.allow: a
lxc.cap.drop: 
lxc.cgroup2.devices.allow: c 10:200 rwm
lxc.mount.entry: /dev/net/tun dev/net/tun none bind,create=file
```
这些代码，可以避免我们在虚拟机中运行docker失败，以及开启tun网卡
打开容器，进入后，首先升级软件包 升级完成后，我们来开启第三方登录
```
nano /etc/ssh/sshd_config
service ssh restart
```
修改完成后   重启相关服务   service ssh restart 利用第三方ssh登录后，我们来进一步优化 设置东八区与中文
```
timedatectl set-timezone Asia/Shanghai
# 追加本地语言配置
echo "zh_CN.UTF-8 UTF-8" >> /etc/locale.gen
# 重新配置本地语言
dpkg-reconfigure locales
# 指定本地语言
export LC_ALL="zh_CN.UTF-8"
#中文的设置
```
重启
安装命令行工具zsh和ohmyzsh插件
```
apt update
apt install zsh git vim curl -y
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
```
配置命令提示工具

Ubuntu的功能是由command-not-found提供的，zsh环境默认不启用，启用的话需要在zsh配置文件~/.zshrc添加
```
nano ~/.zshrc
. /etc/zsh_command_not_found
```
后，source ~/.zshrc
基础工作完成后，我们右键对应的容器，转化为模板即可

## easymosdns安装
上传脚本dns-ui.sh以及prometheus.yml、docker-compose.yml、dns.json
#赋予脚本可执行权限
```
chmod +x dns-ui.sh
```
#执行脚本
```
./dns-ui.sh
```
#配置文件内容替换

#重启程序
```
mosdns service restart
```

#查看是否安装成功
```

mosdns service status
```

创建启动文件所需配置
#创建启动文件所需配置文件夹
```
mkdir -p /home/docker/prometheus/
```

#下载好的文件放入该文件夹

docker安装相关文件
```
docker-compose up -d
```

可视化配置
granf软件配置
修改默认数据库
http://localhost:9090
修改默认语言
面板导入
逐行启用
日志文件优化
crontab -e


在文件末尾添加以下内容
```
0 5 * * * sudo truncate -s 0 /etc/mosdns/mosdns.log && /etc/mosdns/rules/update-cdn
```
