import logging
logger = logging.getLogger(__name__)

def validate(payload: dict, config: dict) -> tuple:
    t = config.get("thresholds", {})
    if payload.get("duplicate") is True:
        logger.warning(f"Duplicate dropped id={payload.get('id')}")
        return False, {}
    if payload.get("dropout") is True:
        logger.warning(f"Dropout dropped id={payload.get('id')}")
        return False, {}
    temp     = payload.get("temp")
    humidity = payload.get("humidity")
    aq       = payload.get("aq", 0)
    gas      = payload.get("gas", 0)
    if temp is None or humidity is None:
        logger.warning("Null values detected")
        return False, {}
    if not (t.get("temp_min",0) <= temp <= t.get("temp_max",50)):
        payload["anomaly"] = True
        payload["anomaly_type"] = "temp_spike"
    elif aq > t.get("aq_max", 3000):
        payload["anomaly"] = True
        payload["anomaly_type"] = "aq_spike"
    elif gas > t.get("gas_max", 3000):
        payload["anomaly"] = True
        payload["anomaly_type"] = "gas_spike"
    else:
        payload["anomaly"] = False
        payload["anomaly_type"] = "none"
    payload["aq_alert"]  = aq  > t.get("aq_max", 3000)
    payload["gas_alert"] = gas > t.get("gas_max", 3000)
    return True, payload
