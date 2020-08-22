#!/bin/bash
#
# 添加监控进程(只在管理节点启动)
#

set -x

if [[ $# -ne 1 ]];then
    echo "Error: Missing arguments."
    echo "Usage:"
    echo "  sh $0 grafana_admin_password"
    exit 1
fi

# 安装配置文件
[[ ! -d "/etc/prometheus" ]] && { echo "Prometheus /etc/prometheus is not existed"; exit 1; }
rm -rf /etc/prometheus/prometheus.yml && touch /etc/prometheus/prometheus.yml
cat >> /etc/prometheus/prometheus.yml <<EOF
# my global config
global:
  scrape_interval:     15s # Set the scrape interval to every 15 seconds. Default is every 1 minute.
  evaluation_interval: 15s # Evaluate rules every 15 seconds. The default is every 1 minute.
  # scrape_timeout is set to the global default (10s).

# Alertmanager configuration
alerting:
  alertmanagers:
  - static_configs:
    - targets:
      # - alertmanager:9093

# Load rules once and periodically evaluate them according to the global 'evaluation_interval'.
rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

# A scrape configuration containing exactly one endpoint to scrape:
# Here it's Prometheus itself.
scrape_configs:
  # The job name is added as a label `job=<job_name>` to any timeseries scraped from this config.
  - job_name: 'ceph-exporter'

    # metrics_path defaults to '/metrics'
    # scheme defaults to 'http'.

    static_configs:
    - targets: ['127.0.0.1:9128']

  - job_name: 'node_exporter'
    static_configs:
    - targets: ['127.0.0.1:9100']

EOF

# 启动进程
systemctl daemon-reload
systemctl start prometheus
systemctl start grafana-server
systemctl start ceph_exporter
systemctl start node_exporter

# Fix ceph_exporter 重启自启动问题
cat >> /usr/lib/systemd/system/ceph_exporter.service <<EOF
[Install]
WantedBy=multi-user.target
EOF

# 添加开机启动
systemctl enable ceph_exporter
systemctl enable node_exporter
systemctl enable prometheus
systemctl enable grafana-server
systemctl daemon-reload

# 修改grafana默认密码
grafana-cli admin reset-admin-password $1
