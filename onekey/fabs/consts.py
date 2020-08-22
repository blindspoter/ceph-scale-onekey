# -*- coding: utf-8 -*-

import os

from onekey.config import PROJECT_PATH

# 集群部署相关配置
CLUSTER_DEPLOY_DIR = "/opt/work/cephcluster"
SCRIPTS_PATH = os.path.join(PROJECT_PATH, 'scripts')

# 目前CEPH集群支持两种硬件设备，分别为浪潮M5 4U服务器，标准浪潮 2U服务器
# 这两种硬件的磁盘规格定义如下(可根据需要扩展)
HDD_2U = ["sdb", "sdc", "sdd", "sde", "sdf", "sdg", "sdh", "sdi", "sdj", "sdk", "sdl", "sdm"]
HDD_4U = ["sdb", "sdc", "sdd", "sde", "sdf", "sdg", "sdh", "sdi", "sdj", "sdk", "sdl", "sdm",
          "sdn", "sdo", "sdp", "sdq", "sdr", "sds", "sdt", "sdu", "sdv", "sdw", "sdx", "sdy",
          "sdz", "sdaa", "sdab", "sdac", "sdad", "sdae", "sdaf", "sdag", "sdah", "sdai", "sdaj",
          "sdak"]
SSD_2U = []
SSD_4U = ["nvme0n1", "nvme1n1"]

CEPH_DASHBOARD_ADMIN_PWD = "admin@123"
GRAFANA_ADMIN_PWD = "admin@123"
