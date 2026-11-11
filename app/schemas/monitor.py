from typing import Any, Dict, List, Optional
from pydantic import BaseModel, root_validator


from uptime_kuma_api import MonitorType, AuthMethod

JSON_QUERY = MonitorType.JSON_QUERY.value
DNS = MonitorType.DNS.value
DEFAULT_JSON_PATH_OPERATOR = "=="
DEFAULT_DNS_PORT = 53


def apply_type_defaults(
    data: Dict[str, Any], existing: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Fill in the values Uptime Kuma 2.x needs but API clients usually leave out.

    `existing` is the stored monitor on update: a default is applied only when
    neither the request nor the stored monitor has a value.
    """
    existing = existing or {}
    monitor_type = data.get("type") or existing.get("type")
    monitor_type = getattr(monitor_type, "value", monitor_type)

    # Kuma 2.x evaluates a json-query monitor with this operator. Without one every
    # check fails with "Invalid condition", so the monitor would be DOWN forever.
    if (
        monitor_type == JSON_QUERY
        and not data.get("jsonPathOperator")
        and not existing.get("jsonPathOperator")
    ):
        data["jsonPathOperator"] = DEFAULT_JSON_PATH_OPERATOR

    if (
        monitor_type == DNS
        and data.get("port") is None
        and existing.get("port") is None
    ):
        data["port"] = DEFAULT_DNS_PORT

    return data


class Monitor(BaseModel):
    type: MonitorType
    name: str
    description: Optional[str] = None
    interval: int = 60
    retryInterval: int = 60
    resendInterval: int = 0
    maxretries: int = 0
    upsideDown: bool = False
    notificationIDList: Optional[List] = None

    # Uptime Kuma 2.x only
    conditions: Optional[List] = None
    retryOnlyOnStatusCodeFailure: Optional[bool] = None

    # HTTP KEYWORD JSON-QUERY
    url: Optional[str] = None
    expiryNotification: bool = False
    ignoreTls: bool = False
    maxredirects: int = 10
    accepted_statuscodes: Optional[List[str]] = None
    proxyId: Optional[int] = None
    method: str = "GET"
    body: Optional[str] = None
    headers: Optional[str] = None
    authMethod: AuthMethod = AuthMethod.NONE
    basic_auth_user: Optional[str] = None
    basic_auth_pass: Optional[str] = None
    authDomain: Optional[str] = None
    authWorkstation: Optional[str] = None
    timeout: Optional[int] = None

    # KEYWORD
    keyword: Optional[str] = None

    # JSON-QUERY
    jsonPath: Optional[str] = None
    jsonPathOperator: Optional[str] = None
    expectedValue: Optional[str] = None

    # DNS PING STEAM MQTT
    hostname: Optional[str] = None

    # DNS STEAM MQTT (defaults to 53 for DNS monitors)
    port: Optional[int] = None

    # DNS
    dns_resolve_server: str = "1.1.1.1"
    dns_resolve_type: str = "A"

    # MQTT
    mqttUsername: Optional[str] = None
    mqttPassword: Optional[str] = None
    mqttTopic: Optional[str] = None
    mqttSuccessMessage: Optional[str] = None

    # SQLSERVER POSTGRES
    databaseConnectionString: Optional[str] = None
    databaseQuery: Optional[str] = None

    # DOCKER
    docker_container: str = ""
    docker_host: Optional[int] = None

    # RADIUS
    radiusUsername: Optional[str] = None
    radiusPassword: Optional[str] = None
    radiusSecret: Optional[str] = None
    radiusCalledStationId: Optional[str] = None
    radiusCallingStationId: Optional[str] = None

    class Config:
        use_enum_values = True

    @root_validator
    def _type_defaults(cls, values):
        return apply_type_defaults(values)


class MonitorUpdate(Monitor):
    type: Optional[MonitorType] = None
    name: Optional[str] = None


class MonitorTag(BaseModel):
    tag_id: int
    value: Optional[str] = ""
