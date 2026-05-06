import paho.mqtt.client as mqtt
import json, time, random, math

client = mqtt.Client()
client.connect("localhost", 1883)
rid = 0
print("Simulator running — sending data every 2 seconds...")

while True:
    rid += 1
    hour = (time.time() % 86400) / 3600
    temp = 21 + 4 * math.sin((hour-6)*math.pi/12) + random.gauss(0,.3)
    hum  = 58 - 0.5 * temp + random.gauss(0, 1.5)
    aq   = int(800 + random.gauss(0, 60))
    gas  = int(600 + random.gauss(0, 40))
    if rid % 100 == 0: aq = 4095
    dropout   = rid % 200 == 0
    duplicate = rid % 150 == 0
    if dropout: temp = None; hum = None
    payload = {
        "device_id": "esp32_aq_monitor",
        "id": rid, "ts": int(time.time()*1000),
        "temp": round(temp,2) if temp else None,
        "humidity": round(hum,2) if hum else None,
        "aq": aq, "gas": gas,
        "room": "living_room",
        "duplicate": duplicate,
        "dropout": dropout
    }
    client.publish("home/air_quality", json.dumps(payload))
    print(f"[{rid}] aq={aq} temp={payload['temp']} gas={gas}")
    time.sleep(2)
