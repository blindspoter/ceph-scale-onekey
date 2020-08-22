#!/bin/bash
#
# 创建CEPH集群
#

set -x

deploy_dir="/opt/work/cephcluster"
[[ -d ${deploy_dir} ]] && { echo "ERROR: cephcluster directory is already exists"; exit 1; }
mkdir ${deploy_dir} && cd ${deploy_dir}

function exit_if_failed()
{
    if [[  $? -ne 0 ]];then
        exit 1
    fi
}

if [[ $# -ne 4 ]];then
    echo "Error: Missing arguments."
    echo "Usage:"
    echo "  sh $0 hostname ip public_network cluster_network"
    exit 1
fi

# 创建集群元数据
ceph-deploy new $1
exit_if_failed

sed -i '/^mon_host/cmon_host = '"$2"'' ceph.conf
cat >> ceph.conf <<EOF
public_network = $3
cluster_network = $4

mon clock drift allowed = 5
mon clock drift warn backoff = 30
mon_max_pg_per_osd=1024
mon_pg_warn_max_per_osd = 1024
mon_pg_warn_max_object_skew = 20

osd pool default size = 1
osd pool default min size = 1
osd pool default pg num = 256
osd pool default pgp num = 256
osd crush chooseleaf type = 1

max open files = 131072
mon allow pool delete = true

[mon]
mon_warn_pg_not_deep_scrubbed_ratio = 0
mon_warn_pg_not_scrubbed_ratio = 0

[mgr]
mgr modules = dashboard

[osd]
bluestore = true
bluestore_cache_autotune = false
bluestore_warn_on_bluefs_spillover=false
osd max write size = 512
osd_max_backfills = 4
osd disk threads = 8
osd_recovery_max_active = 10
osd_recovery_op_priority = 4
osd_recovery_thread_timeout = 120
osd_recovery_thread_suicide_timeout = 600
osd op threads = 16
osd op thread timeout = 100
osd op thread suicide timeout = 600
osd map cache size = 1024
osd map cache bl size = 128
osd mount options xfs = "rw,noexec,nodev,noatime,nodiratime,nobarrier"
osd scrub begin hour = 0
osd scrub end hour = 9
osd_deep_scrub_randomize_ratio = 0.01
osd scrub during recovery = false

[mds]
mds reconnect timeout = 60
mds_session_blacklist_on_timeout = false
mds_session_blacklist_on_evict = false
mds cache memory limit = 10737418240
EOF

ceph-deploy mon create-initial
exit_if_failed

ceph-deploy --overwrite-conf admin $1
exit_if_failed
