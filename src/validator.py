import logging
logger = logging.getLogger(__name__)

def validate(payload: dict, config: dict) -> tuple:
    t = config.get("thresholds", {})
    if payload.get("duplicate") is True:
        logger.warning(f"Duplicate dropped id={payload.get('id')}")
        return False, {}
    aq  = payload.get("aq", 0)
    gas = payload.get("gas", 0)
    temp     = payload.get("temp")
    humidity = payload.get("humidity")
    if temp is None:
        temp = 0.0
    if humidity is None:
        humidity = 0.0
    if aq > t.get("aq_max", 3000):
        payload["anomaly"] = True
        payload["anomaly_type"] = "aq_spike"
    elif gas > t.get("gas_max", 3000):
        payload["anomaly"] = True
        payload["anomaly_type"] = "gas_spike"
    else:
        payload["anomaly"] = False
        payload["anomaly_type"] = "none"
    payload["temp"]     = temp
    payload["humidity"] = humidity
    payload["aq_alert"]  = aq  > t.get("aq_max", 3000)
    payload["gas_alert"] = gas > t.get("gas_max", 3000)
    return True, payload