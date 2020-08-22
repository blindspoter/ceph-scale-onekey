#!/bin/bash
#
# 部署MGR进程
#

set -x

deploy_dir="/opt/work/cephcluster"
[[ ! -d ${deploy_dir} ]] && { exit 1; }
cd ${deploy_dir}

# 获取管理IP(eth0)
manager_ip=`ifconfig eth0 |awk -F '[ ]+' 'NR==2 {print $3}'`

function exit_if_failed()
{
    if [[  $? -ne 0 ]];then
        exit 1
    fi
}

if [[ $# -ne 3 ]];then
    echo "Error: Missing arguments."
    echo "Usage:"
    echo "  sh $0 hostname dashboard_user dashboard_pwd"
    exit 1
fi

# 创建管理进程
ceph-deploy mgr create $1
exit_if_failed

# 配置Dashboard
sleep 5
ceph mgr module enable dashboard
exit_if_failed
ceph dashboard create-self-signed-cert

# 配置dashborad密码
# ceph dashboard ac-user-create $2 $3 administrator  # nautilus
ceph dashboard set-login-credentials $2 $3    # mimic

ceph config set mgr mgr/dashboard/server_addr ${manager_ip}
ceph config set mgr mgr/dashboard/server_port 3443
ceph config set mgr mgr/dashboard/ssl false
ceph mgr module disable dashboard
ceph mgr module enable dashboard
systemctl restart ceph-mgr@$1
exit_if_failed

# 配置集群均衡插件
ceph balancer status
ceph balancer on
ceph osd set-require-min-compat-client luminous
ceph balancer mode upmap

version=`ceph -v`
if [[ ${version} =~ "mimic" ]];then
    ceph config set mgr mgr/balancer/max_misplaced .01
elif [[ ${version} =~ "nautilus" ]];then
    ceph config set mgr target_max_misplaced_ratio .01
fi

systemctl restart ceph-mgr@$1
exit_if_failed
