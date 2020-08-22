#!/bin/bash
#
# 部署OSD进程
# 当存在SSD类型OSD时，需要修改crushmap,添加ssd_rule
#

set -x

function exit_if_failed()
{
    if [[  $? -ne 0 ]];then
        exit 1
    fi
}

ceph osd getcrushmap -o compiled-crushmap
exit_if_failed
crushtool -d compiled-crushmap -o decompiled-crushmap
exit_if_failed
sed -i '/# rules/a \
rule ssd-rule {\
        id 2\
        type replicated\
        min_size 1\
        max_size 10\
        step take default class ssd\
        step chooseleaf firstn 0 type host\
        step emit\
}\
rule hdd-rule {\
        id 1\
        type replicated\
        min_size 1\
        max_size 10\
        step take default class hdd\
        step chooseleaf firstn 0 type host\
        step emit\
}' decompiled-crushmap
exit_if_failed

ip addr

# 如果compiled-new-crushmap没有生成表明集群的OSD状态异常导致
crushtool -c decompiled-crushmap -o compiled-new-crushmap
exit_if_failed
ceph osd setcrushmap -i compiled-new-crushmap
exit_if_failed
rm -rf compiled-crushmap decompiled-crushmap compiled-new-crushmap

# 验证
rulelist=`ceph osd crush rule list`
if [[ ${rulelist} =~ "hdd-rule" ]] && [[ ${rulelist} =~ "ssd-rule" ]];then
    echo "Add rule in crushmap successfull"
else
    echo "Add rule in crushmap failed"
    exit 1
fi