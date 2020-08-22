#!/bin/bash
#
# 部署MDS进程并创建文件系统
#

set -x

deploy_dir="/opt/work/cephcluster"
[[ ! -d ${deploy_dir} ]] && { exit 1; }
cd ${deploy_dir}

function exit_if_failed()
{
    if [[  $? -ne 0 ]];then
        exit 1
    fi
}

if [[ $# -ne 7 ]];then
    echo "Error: Missing arguments."
    echo "Usage:"
    echo "  sh $0 hostname"
    exit 1
fi

# 创建元数据进程
ceph-deploy mds create $1
exit_if_failed

# 创建文件系统
exit_if_failed
# hdd-rule id=1, ssd-rule id=2
if [[ $7 == "ssd-rule" ]];then
    ceph osd pool create $2 $3 $3 replicated hdd-rule
    ceph osd pool create $4 $5 $5 replicated $7
else
    ceph osd pool create $2 $3 $3 replicated
    ceph osd pool create $4 $5 $5 replicated
fi
exit_if_failed
ceph osd pool set $2 size $6
ceph osd pool set $2 min_size 1
ceph osd pool set $4 size $6
ceph osd pool set $4 min_size 1
ceph fs new cephfs $4 $2
exit_if_failed
