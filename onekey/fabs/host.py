# -*- coding: utf-8 -*-

import os
import yaml
from fabric import Connection

from onekey.config import PROJECT_PATH, CLUSTER_NODE_SSH_USER, CLUSTER_NODE_SSH_PWD
from .consts import SCRIPTS_PATH, SSD_2U, SSD_4U
from onekey.libs.logger import log

ssh_scrips = os.path.join(SCRIPTS_PATH, 'ssh.sh')


class Host(Connection):

    def __init__(self, node):
        super(Host, self).__init__(
            node.public_ip,
            user=CLUSTER_NODE_SSH_USER,
            connect_timeout=15,
            connect_kwargs={'password': CLUSTER_NODE_SSH_PWD}
        )

    def exec_cmd(self, cmd):
        try:
            log.info("[RUN CMD] (%s)" % cmd)
            if self.run(cmd, warn=True).failed:
                log.error("[RUN CMD] Exec (%s) error" % cmd)
                return False
            return True
        except Exception as e:
            log.error("[RUN CMD] Exec (%s) error:%s" % (cmd, e))
            return False

    @classmethod
    def hardware_type(cls, node):
        host = cls(node)
        r = host.run("lsblk|grep nvme", hide=True, warn=True)
        if r.stdout.strip():
            return "4U"
        return "2U"

    @classmethod
    def get_ceph_ips(cls):
        system_yml = os.path.join(PROJECT_PATH, 'data/system.yml')
        with open(system_yml) as f:
            system_conf = yaml.safe_load(f)

        c = Connection(
            "172.17.0.1", user=CLUSTER_NODE_SSH_USER,
            connect_kwargs={'password': CLUSTER_NODE_SSH_PWD}
        )

        public_ip, cluster_ip = "", ""
        cfg = "cat /etc/sysconfig/network-scripts/ifcfg-%s | egrep 'IPADDR'"
        if system_conf["hardware_type"] == "2U":
            r = c.run(cfg % "eth2", hide=True, warn=True)
            r = r.stdout.strip()
            public_ip = r.split("=")[1]
            r = c.run(cfg % "eth3", hide=True, warn=True)
            r = r.stdout.strip()
            cluster_ip = r.split("=")[1]
        if system_conf["hardware_type"] == "4U":
            r = c.run(cfg % "eth4", hide=True, warn=True)
            r = r.stdout.strip()
            public_ip = r.split("=")[1]
            r = c.run(cfg % "eth5", hide=True, warn=True)
            r = r.stdout.strip()
            cluster_ip = r.split("=")[1]

        return public_ip, cluster_ip

    @classmethod
    def admin_node(cls):
        yaml_path = os.path.join(PROJECT_PATH, 'data/system.yml')
        with open(yaml_path) as f:
            conf = yaml.safe_load(f)

        node_role = conf["node_role"]
        if node_role != "admin":
            return

        public_ip, _ = cls.get_ceph_ips()
        # TODO: 需要补充节点类
        node = ClusterNode.get_by_ip(public_ip)
        return node

    @classmethod
    def has_ssd(cls, node):
        t = cls.hardware_type(node)
        if t == "4U":
            return True if SSD_4U else False
        if t == "2U":
            return True if SSD_2U else False
        return False

    @classmethod
    def add_hosts(cls, node):
        """
        只能在主节点执行，只在主节点添加hosts
        """
        host = cls(cls.admin_node())
        host.exec_cmd('sed -i "/%s/d" /etc/hosts' % node.hostname)
        host.exec_cmd('echo "%s  %s" >> /etc/hosts' % (node.public_ip, node.hostname))
        return True

    @classmethod
    def sync_ssh(cls, node):
        """
        只能在管理节点执行
        """
        host = cls(cls.admin_node())
        host.exec_cmd("sh %s %s %s '%s'" % (
            ssh_scrips,
            node.hostname,
            CLUSTER_NODE_SSH_USER,
            CLUSTER_NODE_SSH_PWD
        ))

    @classmethod
    def get_ceph_yaml(cls):
        yaml_path = os.path.join(PROJECT_PATH, 'data/ceph.yml')
        with open(yaml_path) as f:
            conf = yaml.safe_load(f)
        return conf
