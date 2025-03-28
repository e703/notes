#!/bin/bash
##基础文件目录创建
mkdir -p /etc/clash/ruleset /etc/clash/ruleset
##基础文件下载
wget -O /etc/clash/geoip.dat https://fastly.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@release/geoip.dat
wget -O /etc/clash/geosite.dat https://fastly.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@release/geosite.dat
wget -O /etc/clash/country.mmdb https://fastly.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@release/country.mmdb
wget -O /etc/clash/ruleset/icloud.yaml https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/icloud.txt
wget -O /etc/clash/ruleset/apple.yaml https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/apple.txt
wget -O /etc/clash/ruleset/Microsoft.yaml https://cdn.jsdelivr.net/gh/zhanyeye/clash-rules-lite@release/microsoft-rules.txt
##基础文件下载完成
