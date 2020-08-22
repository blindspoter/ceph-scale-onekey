# -*- coding: utf-8 -*-

import os
from fabric import Connection

from onekey.config import CLUSTER_NODE_SSH_USER, CLUSTER_NODE_SSH_PWD
from .consts import SCRIPTS_PATH, CLUSTER_DEPLOY_DIR
from .host import Host

clean_cluster_scripts = os.path.join(SCRIPTS_PATH, 'clean_cluster.sh')
node_trans_scripts = os.path.join(SCRIPTS_PATH, 'node_trans.sh')


class ClusterClean(object):
    """
    清理集群
    """

    @classmethod
    def node_transfer(cls):
        """
        转换节点角色，清理掉出厂灌装时多余的依赖
        """
        c = Connection(
            "172.17.0.1", user=CLUSTER_NODE_SSH_USER,
            connect_kwargs={'password': CLUSTER_NODE_SSH_PWD}
        )
        c.run("sh %s" % node_trans_scripts)

    @classmethod
    def clean_cluster(cls, nodes):
        """
        机器清理，保证安装包再次顺利安装
        """
        admin_node = None
        hostnames = []
        for node in nodes:
            hostnames.append(node.hostname)
            if node.node_role == "admin":
                admin_node = node
        hostnames = " ".join(hostnames)

        # 管理节点上清理
        host = Host(admin_node)
        with host.cd(CLUSTER_DEPLOY_DIR):
            host.exec_cmd("ceph-deploy purge %s >/dev/null 2>&1" % hostnames)
            host.exec_cmd("ceph-deploy purgedata %s >/dev/null 2>&1" % hostnames)
            host.exec_cmd("ceph-deploy forgetkeys")
        host.exec_cmd("rm -rf %s" % CLUSTER_DEPLOY_DIR)

        # 所有节点上清理
        for node in nodes:
            host = Host(node)
            host.exec_cmd("sh %s" % clean_cluster_scripts)
