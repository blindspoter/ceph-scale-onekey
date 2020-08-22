#!/bin/bash
#
# 清理集群
#

set -x

# 清理hosts
cat > /etc/hosts <<EOF
127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4
::1         localhost localhost.localdomain localhost6 localhost6.localdomain6

EOF

# 卸载文件系统
mountdir=`cat /proc/mounts | grep "/cephfs/data" | awk '{print $2}'`
umount -lf ${mountdir}

rm -rf /etc/init.d/cephfsumount
rm -rf /etc/rc0.d/S00cephfsumount
rm -rf /etc/rc0.d/K00cephfsumount
rm -rf /etc/rc3.d/S00cephfsumount
rm -rf /etc/rc3.d/K00cephfsumount
rm -rf /etc/rc6.d/S00cephfsumount
rm -rf /etc/rc6.d/K00cephfsumount

# 清理Docker services
docker ps -a | egrep -v "CONTAINER ID" | awk '{print $1}' | xargs -i -t docker stop {}
docker ps -a | egrep -v "CONTAINER ID" | awk '{print $1}' | xargs -i -t docker rm -f {}
docker images | egrep -v "IMAGE ID" | awk '{print $3}' |xargs -i -t docker rmi {}
service docker stop

# 清理监控服务
rm -rf /etc/prometheus/prometheus.yml
yum remove -y prometheus2 grafana ceph_exporter node_exporter

# 清理ceph
rm -rf /var/run/ceph/
rm -rf /var/lib/ceph/
yum remove -y *rados*
yum remove -y *ceph*

# 清理磁盘分区
vgdisplay | grep ceph- | awk '{print $3}' | xargs -i -t vgremove --force {}
# lvdisplay | grep /dev/ceph-* | awk '{print $3}' | xargs -i -t lvremove --force {}
lsblk -l | grep ceph | awk '{print $1}' |xargs -i -t dmsetup remove {}

# 磁盘格式化
lsblk | egrep -vw 'sda' | egrep -v 'sda1|sda2'| grep sd | awk '{print $1}' | xargs -i -t mkfs.xfs -f /dev/{}
if [[ -n "`lsblk | grep nvme`" ]];then
    lsblk | egrep nvme | awk '{print $1}' | xargs -i -t mkfs.xfs -f /dev/{}
fi

# 清理工作区
rm -rf /opt/work/forensics-storage
rm -rf /opt/work/nginx-web
rm -rf /opt/work/nginx_tm
rm -rf /opt/work/pgdata
