import json, logging, os, sys
import yaml
import paho.mqtt.client as mqtt
from validator import validate
from db_writer import DBWriter

def load_config():
    path = os.path.join(os.path.dirname(__file__), "../config/settings.yaml")
    with open(path) as f:
        return yaml.safe_load(f)

def setup_logging(config):
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        level=config["logging"]["level"],
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(config["logging"]["file"]),
            logging.StreamHandler(sys.stdout)
        ]
    )

config = load_config()
setup_logging(config)
logger = logging.getLogger("pipeline")
db = DBWriter(config)

def on_connect(client, userdata, flags, rc):
    logger.info(f"MQTT connected rc={rc}")
    client.subscribe(config["mqtt"]["topic"])

def on_message(client, userdata, msg):
    try:
        raw = json.loads(msg.payload.decode())
        raw["device_id"] = "esp32_aq_monitor"
        ok, clean = validate(raw, config)
        if ok:
            db.write(clean)
    except json.JSONDecodeError as e:
        logger.error(f"Bad JSON: {e}")
    except Exception as e:
        logger.error(f"Error: {e}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(config["mqtt"]["broker"], config["mqtt"]["port"])
logger.info("Pipeline running...")
client.loop_forever()
