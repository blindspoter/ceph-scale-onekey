# -*- coding: utf-8 -*-

"""
当监控服务起来后，需要添加数据源，还有dashboard，接口参考官方文档:
https://community.grafana.com/t/is-there-an-equivalent-http-api-to-import-a-dashboard-from-grafana-com/9581
"""

import os
import requests
import simplejson as json
from requests.auth import HTTPBasicAuth

from .consts import (
    SCRIPTS_PATH, CLUSTER_DEPLOY_DIR, HDD_2U, HDD_4U, SSD_2U, SSD_4U,
    CEPH_DASHBOARD_ADMIN_PWD, GRAFANA_ADMIN_PWD
)
from onekey.libs.logger import log
from .host import Host

cluster_create_scripts = os.path.join(SCRIPTS_PATH, 'create_cluster.sh')
mon_create_scripts = os.path.join(SCRIPTS_PATH, 'create_mon.sh')
mgr_create_scripts = os.path.join(SCRIPTS_PATH, 'create_mgr.sh')
mds_create_scripts = os.path.join(SCRIPTS_PATH, 'create_mds.sh')
osd_create_scripts = os.path.join(SCRIPTS_PATH, 'create_osd.sh')
monitor_add_scripts = os.path.join(SCRIPTS_PATH, 'create_monitor.sh')


class ClusterCreate(object):
    """
    构建集群
    """

    @classmethod
    def create_cluster(cls, node):
        """
        1. 创建cephcluster部署文件夹
        2. 初始化集群配置, 修改集群配置
        3. 初始化秘钥，同步秘钥
        """
        if node.node_role != "admin":
            return False

        conf = Host.get_ceph_yaml()
        cluster = conf.get("cluster")
        public_network = cluster.get("public_network")
        cluster_network = cluster.get("cluster_network")

        host = Host(node)
        r = host.exec_cmd('sh %s %s %s %s %s' % (
            cluster_create_scripts,
            node.hostname,
            node.public_ip,
            public_network,
            cluster_network,
        ))
        return r

    @classmethod
    def add_mon(cls, node):
        """
        增加MON进程
        """

        admin_node = Host.admin_node()
        admin_host = Host(admin_node)
        r = admin_host.exec_cmd('sh %s %s %s' % (
            mon_create_scripts, node.hostname, node.public_ip))
        return r

    @classmethod
    def create_mgr(cls, node):
        """
        1. 创建mgr进程
        2. 初始化dashboard配置(默认管理IP:3443)
        """

        if node.node_role != "admin":
            return False

        host = Host(node)
        r = host.exec_cmd("sh %s %s %s '%s'" % (
            mgr_create_scripts, node.hostname,
            "admin", CEPH_DASHBOARD_ADMIN_PWD))
        return r

    @staticmethod
    def _create_osd(admin_host, node, scale=False):
        hdds = []
        ssds = []
        if Host.hardware_type(node) == "4U":
            hdds = HDD_4U
            ssds = SSD_4U
        elif Host.hardware_type(node) == "2U":
            hdds = HDD_2U
            ssds = SSD_2U

        log.info("Create osd for hddds: %s, ssds: %s" % (hdds, ssds))

        cmd = "ceph-deploy osd create --data /dev/%s %s"
        osd_node_conn = Host(node)
        if hdds:
            for hdd in hdds:
                osd_node_conn.exec_cmd("sleep 5 && mkfs.xfs -f /dev/%s" % hdd)
                r = admin_host.exec_cmd(cmd % (hdd, node.hostname))
                if not r:
                    log.error("Create osd failed: %s" % hdd)
                    return r

        if ssds:
            for ssd in ssds:
                osd_node_conn.exec_cmd("sleep 5 && mkfs.xfs -f /dev/%s" % ssd)
                r = admin_host.exec_cmd(cmd % (ssd, node.hostname))
                if not r:
                    log.error("Create osd failed: %s" % ssd)
                    return r

            # 集群初始节点创建需要修改crushmap, 添加ssd_rule
            # 添加新的节点时，不需要再修改
            if scale:
                return True

            r = admin_host.exec_cmd(
                "sh %s" % osd_create_scripts
            )
            if not r:
                log.error("Create osd failed, add ssd_rule failed")
                return r
        return True

    @classmethod
    def create_osd(cls, node, scale=False):
        """
        1. 创建OSD进程
        """
        admin_node = Host.admin_node()
        admin_host = Host(admin_node)
        with admin_host.cd(CLUSTER_DEPLOY_DIR):
            r = cls._create_osd(admin_host, node, scale=scale)
        return r

    @classmethod
    def create_mds(cls, node):
        """
        1. 创建文件系统进程
        2. 创建文件系统
        """
        conf = Host.get_ceph_yaml()
        fs = conf.get("ceph-fs")
        data_pool = fs.get("data_pool")
        meta_pool = fs.get("meta_pool")

        # 默认副本数为1
        replicated_size = fs.get("replicated_size")

        if node.node_role != "admin":
            return False

        host = Host(node)
        r = host.exec_cmd('sh %s %s %s %s %s %s %s %s' % (
            mds_create_scripts,
            node.hostname,
            data_pool.get("name"),
            data_pool.get("pgnum"),
            meta_pool.get("name"),
            meta_pool.get("pgnum"),
            replicated_size,
            "ssd-rule" if Host.has_ssd(node) else "no-ssd-rule"
        ))
        return r

    @classmethod
    def adjust_replicated_size(cls, replicated_size=2):
        """
        扩容过程中动态增加副本数
        """
        admin_node = Host.admin_node()
        admin_host = Host(admin_node)
        r = admin_host.run("ceph osd pool ls detail -f json", hide=True, warn=True)
        r = r.stdout.strip()
        if not r:
            return
        all_pool_info = json.loads(r)
        for pool_info in all_pool_info:
            if pool_info["size"] == 1:
                log.warn("Adjust replicated size to %s" % replicated_size)
                admin_host.run("ceph osd pool set %s size %s" % (pool_info["pool_name"], replicated_size))

    @classmethod
    def adjust_pg_size(cls):
        """
        扩容过程中动态增加PG
        """
        admin_node = Host.admin_node()
        admin_host = Host(admin_node)
        r = admin_host.run("ceph -s -f json", hide=True, warn=True)
        r = r.stdout.strip()
        if not r:
            return
        ceph_info = json.loads(r)
        osd_num = ceph_info["osdmap"]["osdmap"]["num_osds"]
        pg_num = ceph_info["pgmap"]["num_pgs"]
        # 保证pg_per_osd>30
        if pg_num / osd_num > 32:
            return

        r = admin_host.run("ceph osd pool ls detail -f json", hide=True, warn=True)
        r = r.stdout.strip()
        all_pool_info = json.loads(r)

        # 只扩容cephfs_data的PG数目, 后续算法需要优化
        for pool_info in all_pool_info:
            if pool_info["pool_name"] != "cephfs_data":
                continue
            need_pgs = osd_num * 32
            log.warn("Adjust pg size to %s" % need_pgs)
            admin_host.run("ceph osd pool set %s pg_num %s" % (pool_info["pool_name"], need_pgs))
            admin_host.run("ceph osd pool set %s pgp_num %s" % (pool_info["pool_name"], need_pgs))

    @classmethod
    def add_monitor(cls, node):
        """
        添加监控服务
        """
        host = Host(node)
        r = host.exec_cmd("sh %s '%s'" % (monitor_add_scripts, GRAFANA_ADMIN_PWD))
        return r

    @classmethod
    def add_monitor_datasource(cls):
        """
        添加数据源
        """
        res = requests.get(
            'http://localhost:3000/api/datasources',
            auth=HTTPBasicAuth('admin', GRAFANA_ADMIN_PWD),
            verify=False
        )
        data = res.json()
        if data:
            if data[0].get("type") == "prometheus":
                return True

        prometheus = {
            "name": "prometheus",
            "type": "prometheus",
            "url": "http://localhost:9090",
            "access": "proxy",
            "basicAuth": False
        }
        requests.post(
            'http://localhost:3000/api/datasources',
            data=prometheus,
            auth=HTTPBasicAuth('admin', GRAFANA_ADMIN_PWD),
            verify=False
        )

        res = requests.get(
            'http://localhost:3000/api/datasources',
            auth=HTTPBasicAuth('admin', GRAFANA_ADMIN_PWD),
            verify=False
        )
        data = res.json()
        if data:
            if data[0].get("type") == "prometheus":
                return True
        return False

    @classmethod
    def add_monitor_dashboard(cls):
        """
        添加UI面板
        """
        pass
