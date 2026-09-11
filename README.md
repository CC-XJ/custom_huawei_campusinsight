# custom:com.cc.ext.huawei.campusinsight

**Latest version:** 0.0.4
This extension is built using the Dynatrace Extension 2.0 Framework.
This means it will benefit of additional assets that can help you browse through the data.

## Topology

This extension will create the following types of entities:
* Huawei CampusInsight Device (campusinsight:device)
* Huawei CampusInsight Board (campusinsight:board)
* Huawei CampusInsight Tenant (campusinsight:tenant)

## Metrics

This extension will collect the following metrics:
* Split by Huawei CampusInsight Device, Huawei CampusInsight Board:
  * Board CPU Usage (`custom.huawei.campusinsight.board.cpu.usage`)
    Current CPU usage for Huawei board devices returned by the CampusInsight topn API. (as Percent)
  * Board CPU Usage Maximum (`custom.huawei.campusinsight.board.cpu.usage.max`)
    Maximum CPU usage observed for Huawei board devices returned by the CampusInsight topn API. (as Percent)
* Split by Huawei CampusInsight Tenant:
  * Network Health Total Rate (`custom.huawei.campusinsight.health.total_rate`)
    Overall network health score for the WLAN, aggregated across all health-degree components. (as Percent)
  * Network Health Rate (`custom.huawei.campusinsight.health.rate`)
    Current health rate value from the CampusInsight health-degree API. (as Percent)
  * Success Connection Rate (`custom.huawei.campusinsight.health.success_connection`)
    Percentage of successful connection attempts, from the succesCon field of the health-degree API. (as Percent)
  * Access Time Consumption (`custom.huawei.campusinsight.health.time_consumption`)
    Access time consumption score from the timeCon field of the health-degree API. (as Percent)
  * Roaming Health (`custom.huawei.campusinsight.health.roaming`)
    Roaming health-degree score. (as Percent)
  * Coverage Health (`custom.huawei.campusinsight.health.coverage`)
    Signal coverage health-degree score. (as Percent)
  * Capacity Health (`custom.huawei.campusinsight.health.capacity`)
    Network capacity health-degree score. (as Percent)
  * Throughput Health (`custom.huawei.campusinsight.health.throughput`)
    Throughput health-degree score. (as Percent)

# Configuration

## Feature sets

Feature sets can be used to opt in and out of metric data collection.
This extension groups together metrics within the following feature sets:

* default

