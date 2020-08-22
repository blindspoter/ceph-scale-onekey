#!/bin/bash
#
# 节点角色转换
# 由于出厂安装的是全量包，当节点设置为普通节点时，需要清理多余的安装包，增加安全性

set -x

# 清理文件系统卸载脚本
rm -rf /etc/init.d/cephfsumount
rm -rf /etc/rc0.d/S00cephfsumount
rm -rf /etc/rc0.d/K00cephfsumount
rm -rf /etc/rc3.d/S00cephfsumount
rm -rf /etc/rc3.d/K00cephfsumount
rm -rf /etc/rc6.d/S00cephfsumount
rm -rf /etc/rc6.d/K00cephfsumount

# 清理监控服务
yum remove -y prometheus2 grafana ceph_exporter node_exporter
rm -rf /etc/prometheus/prometheus.yml

# 清理Docker images(3个)
docker rmi docker.arp.defer.cn/forensics/forensics-analysis
docker rmi docker.arp.defer.cn/forensics/nginx_tm
docker rmi docker.arp.defer.cn/forensics/forensics-pcap-analyse

# 清理工作区
rm -rf /opt/work/nginx-web
rm -rf /opt/work/nginx_tm