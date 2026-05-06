import logging
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime, timezone
logger = logging.getLogger(__name__)

class DBWriter:
    def __init__(self, config):
        cfg = config["influxdb"]
        self.client = InfluxDBClient(
            url=cfg["url"], token=cfg["token"], org=cfg["org"])
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.bucket = cfg["bucket"]
        self.org    = cfg["org"]

    def write(self, payload):
        try:
            point = (
                Point("air_quality")
                .tag("device_id",    payload.get("device_id","esp32_aq_monitor"))
                .tag("room",         payload.get("room","living_room"))
                .tag("anomaly_type", payload.get("anomaly_type","none"))
                .field("temperature", float(payload["temp"]))
                .field("humidity",    float(payload["humidity"]))
                .field("air_quality", int(payload["aq"]))
                .field("gas",         int(payload["gas"]))
                .field("anomaly",     bool(payload["anomaly"]))
                .field("aq_alert",    bool(payload["aq_alert"]))
                .field("gas_alert",   bool(payload["gas_alert"]))
                .time(datetime.now(timezone.utc))
            )
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            logger.info(f"Written: temp={payload['temp']} aq={payload['aq']}")
        except Exception as e:
            logger.error(f"DB write failed: {e}")

    def close(self):
        self.client.close()
