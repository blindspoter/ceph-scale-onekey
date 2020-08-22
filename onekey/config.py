# -*- coding: utf-8 -*-

import os

PROJECT_PATH = os.path.dirname(os.path.dirname(__file__))
LOGGER_PATH = os.path.join(PROJECT_PATH, "logs")

CEPH_CONF = "/etc/ceph"
CLUSTER_NODE_SSH_USER = "cephuser"
CLUSTER_NODE_SSH_PWD = "cephuser"
