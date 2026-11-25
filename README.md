# custom:com.cc.ext.huawei.campusinsight

**Latest version:** 0.1.2
This extension is built using the Dynatrace Extension 2.0 Framework.

## Topology

This extension will create the following types of entities:
* Huawei CampusInsight Device (campusinsight:device)
* Huawei CampusInsight Board (campusinsight:board)
* Huawei CampusInsight Tenant (campusinsight:tenant)

## Metrics

The extension collects the following metrics every minute:

* Split by Huawei CampusInsight Device and Board:
  * Board CPU Usage (`custom.huawei.campusinsight.board.cpu.usage`): current CPU usage (Percent).
  * Board CPU Usage Maximum (`custom.huawei.campusinsight.board.cpu.usage.max`): maximum CPU usage (Percent).
* Split by Huawei CampusInsight Device and Interface:
  * Interface Input Bandwidth Usage (`custom.huawei.campusinsight.interface.bandwidth.input.usage`) (Percent).
  * Interface Output Bandwidth Usage (`custom.huawei.campusinsight.interface.bandwidth.output.usage`) (Percent).
  * Interface Send Drop Packets (`custom.huawei.campusinsight.interface.packets.send.drop.count`) (Count).
  * Interface Receive Drop Packets (`custom.huawei.campusinsight.interface.packets.receive.drop.count`) (Count).
  * Interface Bytes Sent (`custom.huawei.campusinsight.interface.bytes.sent`) (Byte).
  * Interface Bytes Received (`custom.huawei.campusinsight.interface.bytes.received`) (Byte).
* Split by Huawei CampusInsight Tenant:
  * Network Health Total Rate (`custom.huawei.campusinsight.health.total_rate`) (Percent).
  * Coverage Health (`custom.huawei.campusinsight.health.coverage`) (Percent).
  * Capacity Health (`custom.huawei.campusinsight.health.capacity`) (Percent).
  * Throughput Health (`custom.huawei.campusinsight.health.throughput`) (Percent).

Interface metrics are queried from the CampusInsight TopN API with a limit of 150 results per measure. The API query filters to HQ devices, then the extension reports only devices whose names contain `HQ` and either `CSW` or `TSW`. Other device names, including ASW, are excluded. Because the API applies its TopN limit before the extension's local filter, the reported set may not include every matching interface when more than 150 HQ interfaces are returned.

The manifest also declares Network Health Rate, Success Connection Rate, Access Time Consumption, and Roaming Health metrics. These are not currently reported by the runtime.

# Configuration

## Feature sets

Feature sets can be used to opt in and out of metric data collection.
This extension groups metrics into the following feature sets:

* `network_telemetry`: board CPU metrics.
* `network_interface`: interface bandwidth, packet-drop, and byte metrics.
* `network_health`: tenant health metrics.

