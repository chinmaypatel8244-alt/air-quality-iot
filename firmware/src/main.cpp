#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include "config.h"

DHT dht(DHT_PIN, DHT_TYPE);
WiFiClient espClient;
PubSubClient client(espClient);
int readingCount = 0;

void connectWiFi() {
  Serial.println("Starting WiFi...");
  Serial.print("Connecting to: ");
  Serial.println(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    attempts++;
    if (attempts > 40) {
      Serial.println("");
      Serial.print("WiFi FAILED! Status code: ");
      Serial.println(WiFi.status());
      attempts = 0;
    }
  }
  Serial.println(" connected!");
  Serial.print("Local IP: ");
  Serial.println(WiFi.localIP());
}

void connectMQTT() {
  while (!client.connected()) {
    Serial.print("Connecting to MQTT...");
    if (client.connect(DEVICE_ID)) {
      Serial.println(" connected!");
    } else {
      Serial.printf("failed rc=%d retry in 3s\n", client.state());
      delay(3000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  dht.begin();
  connectWiFi();
  client.setServer(MQTT_BROKER, MQTT_PORT);
  connectMQTT();
  Serial.println("Setup complete!");
}

void loop() {
  if (!client.connected()) connectMQTT();
  client.loop();
  readingCount++;

  float temp     = dht.readTemperature();
  float humidity = dht.readHumidity();
  int   aq       = analogRead(MQ135_PIN);
  int   gas      = analogRead(MQ2_PIN);

  if (readingCount % 100 == 0) aq = 4095;
  bool dropout = (readingCount % 200 == 0);
  if (dropout) { temp = NAN; humidity = NAN; }
  bool dup = (readingCount % 150 == 0);

  char payload[300];
  if (isnan(temp)) {
    snprintf(payload, sizeof(payload),
      "{\"device_id\":\"%s\",\"id\":%d,\"ts\":%lu,"
      "\"temp\":null,\"humidity\":null,"
      "\"aq\":%d,\"gas\":%d,"
      "\"room\":\"living_room\","
      "\"duplicate\":%s,\"dropout\":true}",
      DEVICE_ID, readingCount, millis(),
      aq, gas, dup?"true":"false");
  } else {
    snprintf(payload, sizeof(payload),
      "{\"device_id\":\"%s\",\"id\":%d,\"ts\":%lu,"
      "\"temp\":%.2f,\"humidity\":%.2f,"
      "\"aq\":%d,\"gas\":%d,"
      "\"room\":\"living_room\","
      "\"duplicate\":%s,\"dropout\":false}",
      DEVICE_ID, readingCount, millis(),
      temp, humidity, aq, gas,
      dup?"true":"false");
  }

  client.publish(MQTT_TOPIC, payload);
  Serial.println(payload);

  if (readingCount % 300 == 0) delay(5000);
  delay(PUBLISH_INTERVAL);
}