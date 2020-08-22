#!/bin/bash
#
# 添加MON进程
#

set -x

function exit_if_failed()
{
    if [[  $? -ne 0 ]];then
        exit 1
    fi
}

if [[ $# -ne 2 ]];then
    echo "Error: Missing arguments."
    echo "Usage:"
    echo "  sh $0 hostname, public_ip"
    exit 1
fi

deploy_dir="/opt/work/cephcluster"
[[ ! -d ${deploy_dir} ]] && { exit 1; }
cd ${deploy_dir}

# 创建管理进程
ceph-deploy mon add $1
exit_if_failed

# 修改集群配置
sed -i "s/^mon_initial_members.*/&,$1/g" ceph.conf
sed -i "s/^mon_host.*/&,$2/g" ceph.conf

# 同步配置到所有集群节点
hostanems=`cat ceph.conf | grep mon_initial_members | awk -F ' = ' '{print $2}'`
for h in ${hostanems//,/ } ; do
  ceph-deploy --overwrite-conf admin ${h}
  exit_if_failed
done
