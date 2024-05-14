# 下载所需lxc容器模板文件
## 编译下载
下载编译文件中带有rootfs字样的文件，上传到PVE服务器上，eg:模板文件夹
```
/var/lib/vz/template/cache
#上传文件夹
```
## 容器创建
命令行创建
```
pct creat 999 local:vztmpl/openwrt-x86-64-generic-rootfs.tar.gz --rootfs local-lvm:1 --ostype unmanaged --hostname openwrt-LXC --arch amd64 --cores 1 --memory 1024 --swap 0 -net0 bridge=vmbr0,name=eth0


pct create *** \                        #“***”是容器编号
        local:vztmpl/***-rootfs.tar.gz \        #“***-rootfs.tar.gz”时CT模板
        --rootfs local-lvm:1 \                        #“1”为虚拟磁盘大小，这里是1G
        --ostype unmanaged \                        #系统类型，之后可在设置文件中修改
        --hostname OpenWrt \                        #容器名称，之后可在设置文件中修改
        --arch amd64 \                                #系统架构，amd64 | arm64 | armhf | i386
        --cores 8 \                                #分配给容器的核心数，我这里分配的是8个，我测试CT模版不需要对某一个容器分配多少，pve会自己调度，所以我通过CT模板建立的虚拟机都是把cpu资源全部分配的。
        --memory 1024 \                                #分配给容器的内存大小，这里是1G。
        --swap 0 \                                #分配给容器的交换区大小，这里是0
        -net0 bridge=vmbr0,name=eth0 -net1 bridge=vmbr1,name=eth1        #我这里分配了两个网卡，bridge=vmbr1对应的是pve网络您创建的虚拟网卡；name=eth1对应的是openwrt中的网卡。
```

## 容器优化
### 容器完善
创建完成后容器，不要开机，进入对应容器的选项
勾选一下选项
- 嵌套
- nfs
- smb
- fuse
### 容器配置文件
进入pve控制台，进入/etc/pve/lxc文件夹，修改对应的配置文件，添加以下内容
```
lxc.apparmor.profile: unconfined
lxc.cgroup.devices.allow: a
lxc.cap.drop: 
lxc.cgroup2.devices.allow: c 10:200 rwm
lxc.mount.entry: /dev/net/tun dev/net/tun none bind,create=file
```
