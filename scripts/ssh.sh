#!/bin/bash
#
# 同步SSH秘钥，保证从admin-node能免密登录到其他node
#

set -x

current=$(cd `dirname $0`; pwd)

function exit_if_failed()
{
    if [[  $? -ne 0 ]];then
        exit 1
    fi
}

if [[ $# -ne 3 ]];then
    echo "Error: Missing arguments."
    echo "Usage:"
    echo "  sh $0 hostname user pwd"
    exit 1
fi

[[ ! -f /root/.ssh/id_rsa ]] && yes y|ssh-keygen -t rsa -N '' -f /root/.ssh/id_rsa

[[ -f ${current}/ssh-copy.exp ]] && rm -rf ${current}/ssh-copy.exp
touch ${current}/ssh-copy.exp
cat >> ${current}/ssh-copy.exp<<EOF
#!/usr/bin/expect

if {[llength \$argv] != 3} {
  puts "Usage error,use ssh-cppy-id.exp server user pwd"
  exit 1
}

set serv [lindex \$argv 0]
set user [lindex \$argv 1]
set pwd [lindex \$argv 2]
set timeout 100

spawn ssh-copy-id -f \${user}@\${serv}
expect {
  {connecting (yes/no)? } {send "yes\n";exp_continue}
  {password: } {send \${pwd}\n;exp_continue}
  eof {wait}
  timeout {puts timeout}
}

EOF

chmod +x ${current}/ssh-copy.exp
${current}/ssh-copy.exp $1 $2 $3
exit_if_failed
