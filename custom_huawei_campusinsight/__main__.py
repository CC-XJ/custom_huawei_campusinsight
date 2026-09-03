import json
import ssl
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib import error, parse, request

from dynatrace_extension import Extension, Status, StatusValue

# CampusInsight's default cert is self-signed (original curl used -k).
# There's no verify_ssl field in activationSchema.json yet, so this is a configurable field instead of leaving it silently insecure.
_INSECURE_SSL_CONTEXT = ssl.create_default_context()
_INSECURE_SSL_CONTEXT.check_hostname = False
_INSECURE_SSL_CONTEXT.verify_mode = ssl.CERT_NONE

_EXPIRY_BUFFER_SECONDS = 60

LOOKBACK_MINUTES = 15
LOGIN_PATH = "/rest/plat/smapp/v1/oauth/token"
TOPN_PATH = "/rest/pmservice/v2/openapi/topn"
HEALTH_PATH = "/rest/campuswlanqualityservice/v1/expmonitor/overview/rate"


class ExtensionImpl(Extension):
    def initialize(self):
        self.extension_name = "custom_huawei_campusinsight"
        self._session_cache: dict[str, tuple[str, datetime]] = {} # base_url -> (access_session, expires_at)
        self.schedule(self.query_campusinsight, timedelta(minutes=LOOKBACK_MINUTES))


    def query_campusinsight(self):
        self.logger.info("Running Huawei CampusInsight query.")

        for endpoint in self.activation_config["endpoints"]:
            self._query_endpoint(endpoint)


    def _query_endpoint(self, endpoint: dict[str, Any]):
        base_url = endpoint.get("url", "").strip("/")
        tenant_id = endpoint.get("tenantID", "").strip()
        username = endpoint.get("username", "").strip()
        password = endpoint.get("password", "").strip()

        # 【Guardrail】 Check for empty input fields
        if not base_url:
            self.logger.warning("Skipping endpoint without a URL")
            return

        if not tenant_id:
            self.logger.warning("Skipping endpoint %s without a tenant ID", base_url)
            return
        
        if not username or not password:
            self.logger.warning("Skipping endpoint %s without a username/password.", base_url)
            return

        # 【Get Access Token】Call method to obtain access session token
        try:
            access_session = self._get_session(base_url, username, password)

            self.logger.info(
                "Login succeeded for %s (session starts with %s...)",
                base_url,
                access_session[:8],
            )

        except error.URLError as exc:
            self.logger.error("Login to %s failed: %s", base_url, exc)
            return
        
        except Exception as exc:
            self.logger.error("Unexpected error logging into %s: %s", base_url, exc)
            return


        # 【Extract Telemetry】 Fetch Huawei iMaster CPU Usage (Telemetry)
        try:
            resultData = self._fetch_board_cpu_usage(base_url, access_session)

            self.logger.info(
                "CPU usage fetch succeeded for %s (%d rows)", base_url, len(resultData)
            )

            # 【Report Telemetry】Report fetched telemtry metrics to Dynatrace
            for row in resultData:
                self._report_telemetry(row, tenant_id)

        except error.URLError as exc:
            self.logger.error("Request to %s failed: %s", base_url, exc)

        except Exception as exc:
            self.logger.error("Unexpected error querying %s: %s", base_url, exc)

        # 【Extract Health】 Fetch Huawei iMaster Network Health
        try:
            health_data = self._fetch_network_health(base_url, access_session, tenant_id)

            self.logger.info("Health fetch succeeded for %s", base_url)

            # 【Report Health】Report fetched network health metrics to Dynatrace
            self._report_health(health_data, tenant_id)

        except error.URLError as exc:
            self.logger.error("Health request to %s failed: %s", base_url, exc)

        except Exception as exc:
            self.logger.error("Unexpected error querying health for %s: %s", base_url, exc)

    def _login(self, base_url: str, username: str, password: str) -> tuple[str, int]:

        reqData = json.dumps({
            "grantType": "password",
            "userName": username,
            "value": password,
        }).encode("utf-8")

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json;charset=UTF-8",
        }

        req = request.Request(
            f"{base_url}{LOGIN_PATH}",
            data=reqData,
            headers=headers,
            method="PUT"
        )

        try:
            with request.urlopen(req, timeout=30, context=_INSECURE_SSL_CONTEXT) as response:
                resBody = json.loads(response.read())
        except error.HTTPError as e:
            body = e.read().decode(errors="replace")
            self.logger.error("Login HTTP %s: %s", e.code, body)
            raise

        access_session = resBody.get("accessSession")
        expires_in = resBody.get("expires")

        if not access_session:
            raise RuntimeError(f"Login response did not include accessSession: {resBody}")
        if not expires_in:
            raise RuntimeError(f"Login response did not include expires: {resBody}")

        return access_session, expires_in

    def _get_session(self, base_url: str, username: str, password: str) -> str:
        cached = self._session_cache.get(base_url)

        # Return session token if it's still valid
        if cached:
            access_session, expires_at = cached
            if datetime.now(timezone.utc) < expires_at:
                return access_session

        # If token doesn't exist or expired, call login method
        access_session, expires_in = self._login(base_url, username, password)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds = max(expires_in - _EXPIRY_BUFFER_SECONDS, 0))
        self._session_cache[base_url] = (access_session, expires_at)
        return access_session

    def _fetch_board_cpu_usage(self, base_url: str, access_session: str) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc)
        begin = now - timedelta(minutes=LOOKBACK_MINUTES)

        # 【Set Parameter】Condition parameter for Huawei iMaster CPU Usage endpoint
        condition = {
            "measureUnit": "dcn_board",
            "measure": "dcn_board_cpu_usage",
            "beginTime": int(begin.timestamp() * 1000),
            "endTime": int(now.timestamp() * 1000),
            "isAbnormal": False,
            "limit": 1000, 
            "filters": {"id": ["/"], "level": [0], "dcn_filter_ne_name": ["HQ"],},
            "supportOperate": [],
        }

        query_string = parse.urlencode({"condition": json.dumps(condition)})
        full_url = f"{base_url}{TOPN_PATH}?{query_string}"

        headers = {
            "Accept": "application/json",
            "X-Auth-Token": access_session,
        }

        req = request.Request(full_url, headers=headers, method="GET")

        with request.urlopen(req, timeout=30, context=_INSECURE_SSL_CONTEXT) as response:
            resBody = response.read()

        json_resBody = json.loads(resBody)

        if json_resBody.get("error_code") not in (0, "0"):
            raise RuntimeError(f"CampusInsight API error: {json_resBody.get('error_msg')}")

        resultData = json_resBody.get("resultData", [])

        if len(resultData) >= condition["limit"]:
            self.logger.warning(
                "CampusInsight topN response for %s returned %d rows (limit=%d) — "
                "results may be truncated if more boards exist",
                base_url, len(resultData), condition["limit"],
            )

        filtered_resultData = [
            row for row in resultData
            if self._filter_device_name(row.get("dcn_board_ne_name", ""))
        ]

        self.logger.debug(
            "CampusInsight %s: %d/%d boards matches HQ+CSW/TSW filter",
            base_url, len(filtered_resultData), len(resultData),
        )
        
        return filtered_resultData

    def _filter_device_name(self, name: str) -> bool:
        """Return True if the device is an HQ core/top switch (CSW or TSW)."""
        name = name.upper()

        return "HQ" in name and ("CSW" in name or "TSW" in name)

    def _report_telemetry(self, row: dict[str, Any], tenant_id: str):
        raw_id = row.get("id", "")

        if not raw_id:
            self.logger.warning("Skipping board with missing id for tenant %s: %r", tenant_id, row)
            return

        dimensions = {
            "tenant_id": tenant_id,
            "device_name": row.get("dcn_board_ne_name", "unknown"),
            "device_ip": row.get("dcn_board_ne_ip", "unknown"),
            "board_id": raw_id or "unknown",
        }

        meas_value = row.get("meas_value")

        # Report board cpu usage to Dynatrace
        if meas_value is not None:
            try:
                self.report_metric(
                    "custom.huawei.campusinsight.board.cpu.usage",
                    float(meas_value),
                    dimensions = dimensions
                )
            except (TypeError, ValueError):
                self.logger.warning("Non-numeric meas_value for board %s: %r", raw_id, meas_value)

        maximum = row.get("maximum")

        # Report board maximum cpu usage to Dynatrace
        if maximum is not None:
            try:
                self.report_metric(
                    "custom.huawei.campusinsight.board.cpu.usage.max",
                    float(maximum),
                    dimensions=dimensions,
                )
            except (TypeError, ValueError):
                self.logger.warning("Non-numeric maximum for board %s: %r", raw_id, maximum)

    def _fetch_network_health(self, base_url: str, access_session: str, tenant_id: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        begin = now - timedelta(minutes=LOOKBACK_MINUTES)

        parameter = {
            "id": "/",
            "regionType": "site",
            "level": 0,
            "tenantId": tenant_id,
            "startTime": int(begin.timestamp() * 1000),
            "endTime": int(now.timestamp() * 1000),
        }

        query_string = parse.urlencode({"param": json.dumps(parameter)})
        full_url = f"{base_url}{HEALTH_PATH}?{query_string}"

        headers = {
            "Accept": "application/json",
            "X-Auth-Token": access_session
        }

        req = request.Request(full_url, headers = headers, method = "GET")

        with request.urlopen(req, timeout=30, context=_INSECURE_SSL_CONTEXT) as response:
            resBody = response.read()

        json_resBody = json.loads(resBody)

        if json_resBody.get("resultCode") not in (None, 0, "0"):
            raise RuntimeError(f"CampusInsight health API error: {json_resBody.get('errorDes')}")

        return json_resBody.get("data", {})

    def _report_health(self, health_data: dict[str, Any], tenant_id: str):
        dimensions = {"tenant_id": tenant_id}

        values = health_data.get("values", {})

        field_map = {
            "custom.huawei.campusinsight.health.total_rate": (health_data, "totalRate"),
            "custom.huawei.campusinsight.health.rate": (values, "rate"),
            # "custom.huawei.campusinsight.health.success_connection": (values, "succesCon"),
            # "custom.huawei.campusinsight.health.time_consumption": (values, "timeCon"),
            # "custom.huawei.campusinsight.health.roaming": (values, "roaming"),
            "custom.huawei.campusinsight.health.coverage": (values, "coverage"),
            "custom.huawei.campusinsight.health.capacity": (values, "capacity"),
            "custom.huawei.campusinsight.health.throughput": (values, "throughput"),
        }

        for metric_key, (source, field) in field_map.items():
            raw_value = source.get(field)

            if raw_value is None:
                self.logger.warning("Missing %s in health response for tenant %s", field, tenant_id)
                continue

            try:
                self.report_metric(metric_key, float(raw_value), dimensions=dimensions)

            except (TypeError, ValueError):
                self.logger.warning("Non-numeric %s for tenant %s: %r", field, tenant_id, raw_value)


    def fastcheck(self):
        return Status(StatusValue.OK)

def main():
    ExtensionImpl().run()

if __name__ == "__main__":
    main()
