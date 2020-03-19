# Debian 9 下安装 MySQL 5.7
## 1.在线安装
### 1.1 配置apt-get源
-debian下安装软件的指令为apt-get，在使用apt-get安装MySQL之前，需要先下载MySQL官网提供的DEB包，以将MySQL的仓库添加到apt-get的源中.
- 打开网站[
MySQL APT Respository](https://dev.mysql.com/downloads/repo/apt/ "MySQL APT Respository") 
![MySQL-Download](https://s1.ax1x.com/2020/03/19/8r60G6.png)
- 点击Download，跳转到下载页面:MySQL-Download
![8r6sMD.png](https://s1.ax1x.com/2020/03/19/8r6sMD.png)
- 右键点击No thanks，just start my download复制链接

### 1.2 在线安装
打开debian的shell，进入你的工作目录
`cd ~`

使用wget指令下载deb文件(刚刚复制的链接)
`wget https://dev.mysql.com/get/mysql-apt-config_0.8.15-1_all.deb`
下载之后可以使用ls查看到刚刚下载的文件

当然你下载下来的文件的版本号可能不一定是这个，一切以你下载的结果为准，接下来使用dpkg指令添加该文件进apt-get的源
`sudo dpkg -i ./mysql-apt-config_0.8.9-1_all.deb`

完成后会弹出一个mysql的源的配置界面
![8rgXvT.png](https://s1.ax1x.com/2020/03/19/8rgXvT.png)


MySQL源配置界面
我们什么都不用动，方向键移动到OK回车即可，接下来使用apt-get的update指令更新源

sudo apt-get update
完成更新后，就可以正式开始mysql的安装了

安装
使用apt-get指令安装MySQL

sudo apt-get install mysql-server
200多M，然后就是漫长的等待......中途会让输入root密码，自己输入一个记住就行了

基本操作
开启MySQL服务

sudo service mysql start
关闭服务

sudo service mysql stop
重启服务

sudo service mysql restart
尝试登陆
mysql -u root -p
输入密码即可登陆到mysql

一些方便开发的配置
因为MySQL刚刚安装完成的时候是不允许从远程访问的，这对于开发十分不友好，另外，MySQL刚刚安装完成的时候，是只能使用root用户登录的，这也是一个不安全的地方，所以我们应该建立一个用于开发的数据库账户，并且为它设置远程访问权限，当然，在真正投入生成环境之后，我们应该移除远程访问的权限

首先，先创建一个新用户，在这之前要先登录MySQL

mysql -u root -p
输入密码登录之后，使用如下指令来新建一个用户

mysql> CREATE USER 'username'@'%' IDENTIFIED BY 'password';
完成之后使用如下指令为该用户分配所有权限

mysql> GRANT ALL PRIVILEGES ON *.* TO 'username'@'%';
接着刷新权限即可使用新用户在任意host登录数据库

mysql> FLUSH PRIVILEGES;
如果还是不行的话，打开下面的文件

sudo vim /etc/mysql/mysql.conf.d/mysqlld.cnf
把bind-adress那一行的127.0.0.1改成0.0.0.0(当然，投入生产时记得改回来！)

  # By default we only accept connections from localhost
- bind-address    = 127.0.0.1
+ bind-address    = 0.0.0.0
即可



UPDATE mysql.user SET authentication_string = PASSWORD('mypassword'), plugin = 'mysql_native_password' WHERE User = 'root' AND Host = 'localhost';
MariaDB [(none)]> FLUSH PRIVILEGES;
MariaDB [(none)]> exit




卸载：

sudo dpkg --get-selections | grep mysql


使用purge卸载:

sudo apt-get --purge remove mysql-server
sudo apt-get --purge remove mysql-client
sudo apt-get --purge remove mysql-common

这样就可以卸载完成了

3
使用以下命令卸载不需要的安装包:

sudo apt-get autoremove

sudo apt-get autoclean

删除mysql配置文件是否清除(如果没有清除):

rm /etc/mysql/ -rf
rm /var/lib/mysql/ -rf


方法/步骤2 重新安装
1
安装命令 :

sudo apt-get install mysql-server mysql-client

mysql 的 启动/关闭/重启命令:

service mysql start 启动

service mysql stop 关闭

service mysql restart 重启

2
在debian上安装mysql 使用的是 MariaDB 

默认只能root用户登录和空密码登录

设置 普通用户登录命令:

在root用户下:mysql -uroot -p 登入mysql (直接enter)

debian mysql 安装和 卸载
3
进入到mysql数据库中,依次输入以下命令:

use mysql  ➠ select user,plugin from user; ↪︎

update mysql.user set plugin='' where User='root'; ↪︎

flush privileges;

4
允许远程连接并配置密码:

在debian中mysql的配置文件在/etc/mysql/mariadb.conf.d/50-server.cnf中,

sudo vi /etc/mysql/mariadb.conf.d/50-server.cnf

将 bind-address=127.0.0.1 注释掉 开头加#

debian mysql 安装和 卸载
5
登录mysql 并输入以下命令:

grant all privileges on *.* to 'root'@'%' identified by 'mysql' with grant option;

flush privileges;

6
重启 mysql:

service mysql restart

7
end..........

能力有限,暂时到这里了






插入网络图片01（MD专用格式）
[![8rwClj.png](https://s1.ax1x.com/2020/03/19/8rwClj.png)](https://imgchr.com/i/8rwClj)




