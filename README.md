# Huawei CampusInsight Dynatrace Extension

A Dynatrace custom extension for collecting operational telemetry from Huawei iMaster CampusInsight and feeding it into Dynatrace as custom metrics and topology data.

This extension connects to the CampusInsight API, authenticates against the Huawei iMaster instance, gathers board-level CPU usage and network health indicators, and reports them as Dynatrace custom metrics with tenant, device, and board dimensions.

## Overview

The extension is designed for environments where Huawei CampusInsight is used to monitor WLAN and campus network health. It periodically queries:

- Board performance data from the CampusInsight TopN API
- Network health and quality metrics from the CampusInsight health-degree API
- Tenant, device, and board relationships for topology modeling in Dynatrace

It is implemented as a remote Python extension for Dynatrace and is intended for use in environments where the Huawei platform exposes a self-signed certificate and requires token-based authentication.

## What it collects

### Board CPU metrics
The extension filters for HQ core/top switch devices and exports CPU usage metrics for matching boards.

- custom.huawei.campusinsight.board.cpu.usage
- custom.huawei.campusinsight.board.cpu.usage.max

Dimensions:
- tenant_id
- device_name
- device_ip
- board_id

### Network health metrics
The extension also reports health indicators for the tenant.

- custom.huawei.campusinsight.health.total_rate
- custom.huawei.campusinsight.health.rate
- custom.huawei.campusinsight.health.coverage
- custom.huawei.campusinsight.health.capacity
- custom.huawei.campusinsight.health.throughput

These metrics are grouped by tenant and give visibility into overall network health and experience quality.

## Architecture

The project includes:

- A Dynatrace extension definition in [extension/extension.yaml](extension/extension.yaml)
- Activation schema for remote endpoint configuration in [extension/activationSchema.json](extension/activationSchema.json)
- The Python extension implementation in [custom_huawei_campusinsight/__main__.py](custom_huawei_campusinsight/__main__.py)
- Package metadata in [setup.py](setup.py)

The Python code:

1. Reads the configured CampusInsight endpoints from the Dynatrace activation config.
2. Logs in using the Huawei OAuth token endpoint.
3. Caches access sessions to avoid repeated logins.
4. Pulls board CPU and health data for recent time windows.
5. Converts values to Dynatrace custom metrics.
6. Publishes topology for tenant, device, and board entities.

## Configuration

The extension expects one or more CampusInsight endpoints with the following fields:

- url
- tenantID
- username
- password

## Installation and local development

Install the package in editable mode:

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

The package requires Python 3.10+ and the Dynatrace extension SDK:

```bash
pip install "dt-extensions-sdk>=1.8.0"
```

## Running the extension

The project is designed to run as a Dynatrace remote extension, not as a standalone app. The entry point is:

```bash
python -m custom_huawei_campusinsight
```

This executes the extension logic and schedules the polling routines for CampusInsight telemetry collection.

## Notes

- Session tokens are cached and refreshed before expiry.
- API requests use a short lookback window to keep metric collection focused and current.
- Board filtering is intentionally narrow and targets HQ CSW/TSW devices to reduce noise.
- The extension is aimed at Huawei iMaster CampusInsight operational monitoring use cases.

## Project status

This project is a custom monitoring extension for Dynatrace and is currently tailored to Huawei CampusInsight data collection patterns.

