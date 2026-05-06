#ifndef CONFIG_H
#define CONFIG_H

// ── WiFi credentials ─────────────────────────────────────────
#define WIFI_SSID     "Cvs"
#define WIFI_PASSWORD "Kanan@1234"

// ── MQTT broker ───────────────────────────────────────────────
// Use your LOCAL network IP — run these to find it:
//   Mac:     ipconfig getifaddr en0
//   Windows: ipconfig  (look for IPv4 Address under WiFi)
// It must start with 192.168.x.x or 10.x.x.x
// 150.250.x.x is your university public IP — it will NOT work
#define MQTT_BROKER   "10.0.0.199"
#define MQTT_PORT     1883
#define MQTT_TOPIC    "home/air_quality"
#define DEVICE_ID     "esp32_aq_monitor"

// ── Sensor pins ───────────────────────────────────────────────
#define DHT_PIN       4    // DHT22 DATA wire → ESP32 GPIO4
#define DHT_TYPE      DHT22
#define MQ135_PIN     34   // MQ-135 AOUT → ESP32 GPIO34 (analog input)
#define MQ2_PIN       35   // MQ-2 AOUT   → ESP32 GPIO35 (analog input)

// ── Timing ────────────────────────────────────────────────────
#define PUBLISH_INTERVAL 2000  // milliseconds between readings

#endif