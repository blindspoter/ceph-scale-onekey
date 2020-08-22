#!/bin/bash

mkdir -p /sys/fs/cgroup/cpuset/ceph
# cup number : 0,1,2,3 = 0-3
echo 15-39 > /sys/fs/cgroup/cpuset/ceph/cpuset.cpus
# NUMA node
echo 0 > /sys/fs/cgroup/cpuset/ceph/cpuset.mems
osd_pid_list=$(ps aux | grep osd | grep -v grep | awk '{print $2}')
for osd_pid in ${osd_pid_list}
do
    echo ${osd_pid} > /sys/fs/cgroup/cpuset/ceph/cgroup.procs
done