/**
 * Smart Home 'Rumah' — Firmware ESP32 Native C++ (PlatformIO)
 * Mendukung MQTT LWT, Kontrol Relay/Lampu, Alarm Gas Otonom (Non-Blocking),
 * Telemetri Berkala, dan Update OTA Terproteksi.
 */

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <ArduinoOTA.h>
#include <esp_task_wdt.h>

#include "config.h"

#if __has_include("secrets.h")
#include "secrets.h"
#else
#include "secrets.h.example"
#endif

// --- VARIABEL GLOBAL & OBJEK KONEKSI ---
WiFiClient espClient;
PubSubClient mqttClient(espClient);

// Status Output Lokal
bool stateLampTengah = false;
bool stateLampDapurTamu = false;
bool stateLampKamar = false;
bool stateRelay = false;
bool stateBuzzer = false;

// Status Sensor
uint16_t currentGasRaw = 0;
bool currentIsDark = false;
bool isGasAlarmActive = false;

// Pewaktu Asinkron (Non-Blocking Millis)
uint32_t lastTelemetryTime = 0;
uint32_t lastWifiRetryTime = 0;
uint32_t lastMqttRetryTime = 0;
uint32_t lastBuzzerToggleTime = 0;
bool buzzerBeepState = false;

// Topik MQTT
String topicAvailability = String("home/") + DEVICE_ID + "/availability";
String topicCmd          = String("home/") + DEVICE_ID + "/cmd";
String topicState        = String("home/") + DEVICE_ID + "/state";
String topicEvent        = String("home/") + DEVICE_ID + "/event";
String topicAck          = String("home/") + DEVICE_ID + "/ack";

// Deklarasi Fungsi
void setupPins();
void setupWifi();
void setupMqtt();
void setupOTA();
void reconnectMqtt();
void handleMqttMessage(char* topic, byte* payload, unsigned int length);
void publishState();
void publishEvent(const char* eventName, const char* channel, float value);
void updateHardwareOutputs();
void processSensorsAndAlarm();

void setup() {
    Serial.begin(115200);
    delay(500);
    Serial.println("\n[RUMAH] Menginisialisasi Firmware ESP32...");

    setupPins();

    // 1. Inisialisasi Hardware Watchdog Timer (WDT)
    esp_task_wdt_config_t wdtConfig = {
        .timeout_ms = WDT_TIMEOUT_SECONDS * 1000,
        .idle_core_mask = (1 << 0) | (1 << 1),
        .trigger_panic = true,
    };
    esp_task_wdt_init(&wdtConfig);
    esp_task_wdt_add(NULL);

    // 2. Setup Jaringan & Layanan
    setupWifi();
    setupMqtt();
    setupOTA();

    Serial.println("[RUMAH] Inisialisasi selesai. Memulai loop kontrol utama.");
}

void loop() {
    // Reset Hardware Watchdog pada setiap iterasi loop
    esp_task_wdt_reset();

    // 1. Tangani update OTA
    ArduinoOTA.handle();

    // 2. Baca sensor dan proses sirine lokal (berjalan independen walau tanpa jaringan)
    processSensorsAndAlarm();

    // 3. Manajemen Koneksi WiFi (Non-blocking reconnect)
    uint32_t now = millis();
    if (WiFi.status() != WL_CONNECTED) {
        if (now - lastWifiRetryTime > 10000) {
            lastWifiRetryTime = now;
            Serial.println("[WiFi] Koneksi terputus. Mencoba menghubungkan kembali...");
            WiFi.disconnect();
            WiFi.reconnect();
        }
    } else {
        // 4. Manajemen Koneksi MQTT (hanya jika WiFi terhubung)
        if (!mqttClient.connected()) {
            if (now - lastMqttRetryTime > 5000) {
                lastMqttRetryTime = now;
                reconnectMqtt();
            }
        } else {
            mqttClient.loop();
        }
    }

    // 5. Pengiriman Telemetri Berkala (Setiap 10 Detik)
    if (mqttClient.connected() && (now - lastTelemetryTime >= TELEMETRY_INTERVAL_MS)) {
        lastTelemetryTime = now;
        publishState();
    }
}

void setupPins() {
    pinMode(PIN_LAMP_TENGAH, OUTPUT);
    pinMode(PIN_LAMP_DAPUR_TAMU, OUTPUT);
    pinMode(PIN_LAMP_KAMAR, OUTPUT);
    pinMode(PIN_BUZZER, OUTPUT);
    pinMode(PIN_RELAY, OUTPUT);

    pinMode(PIN_MQ2_GAS, INPUT);
    pinMode(PIN_LDR_DIGITAL, INPUT);

    // Set initial hardware outputs
    updateHardwareOutputs();
}

void updateHardwareOutputs() {
    digitalWrite(PIN_LAMP_TENGAH, stateLampTengah ? HIGH : LOW);
    digitalWrite(PIN_LAMP_DAPUR_TAMU, stateLampDapurTamu ? HIGH : LOW);
    digitalWrite(PIN_LAMP_KAMAR, stateLampKamar ? HIGH : LOW);

    // Relay aktif LOW
    digitalWrite(PIN_RELAY, stateRelay ? RELAY_ACTIVE_LEVEL : RELAY_INACTIVE_LEVEL);

    // Buzzer dikontrol oleh alarm atau manual command
    if (!isGasAlarmActive) {
        digitalWrite(PIN_BUZZER, stateBuzzer ? HIGH : LOW);
    }
}

void processSensorsAndAlarm() {
    // Baca sensor gas (analog) & sensor cahaya (digital)
    currentGasRaw = analogRead(PIN_MQ2_GAS);
    currentIsDark = (digitalRead(PIN_LDR_DIGITAL) == HIGH);

    uint32_t now = millis();

    // Deteksi gas darurat
    if (currentGasRaw >= GAS_RAW_THRESHOLD) {
        if (!isGasAlarmActive) {
            isGasAlarmActive = true;
            Serial.printf("[ALARM GAS] Nilai gas tinggi terdeteksi: %u >= %u!\n", currentGasRaw, GAS_RAW_THRESHOLD);
            publishEvent("gas_alarm", "mq2", currentGasRaw);
        }

        // Sirine non-blocking berbunyi intermiten (200ms ON, 200ms OFF)
        if (now - lastBuzzerToggleTime >= 200) {
            lastBuzzerToggleTime = now;
            buzzerBeepState = !buzzerBeepState;
            digitalWrite(PIN_BUZZER, buzzerBeepState ? HIGH : LOW);
        }
    } else {
        if (isGasAlarmActive) {
            isGasAlarmActive = false;
            Serial.println("[ALARM GAS] Level gas kembali normal.");
            digitalWrite(PIN_BUZZER, stateBuzzer ? HIGH : LOW);
        }
    }
}

void setupWifi() {
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    Serial.printf("[WiFi] Menghubungkan ke %s...", WIFI_SSID);
    lastWifiRetryTime = millis();
}

void setupMqtt() {
    mqttClient.setServer(MQTT_HOST, MQTT_PORT);
    mqttClient.setCallback(handleMqttMessage);
    mqttClient.setBufferSize(1024);
}

void setupOTA() {
    ArduinoOTA.setHostname(DEVICE_ID);
    ArduinoOTA.setPassword(OTA_PASSWORD);

    ArduinoOTA.onStart([]() {
        String type = (ArduinoOTA.getCommand() == U_FLASH) ? "sketch" : "filesystem";
        Serial.println("[OTA] Memulai update: " + type);
    });
    ArduinoOTA.onEnd([]() {
        Serial.println("\n[OTA] Update selesai!");
    });
    ArduinoOTA.onError([](ota_error_t error) {
        Serial.printf("[OTA] Error[%u]\n", error);
    });

    ArduinoOTA.begin();
    Serial.println("[OTA] Siap menerima update over-the-air.");
}

void reconnectMqtt() {
    Serial.printf("[MQTT] Mencoba terhubung ke broker %s:%d...\n", MQTT_HOST, MQTT_PORT);

    // Sambungkan dengan Last Will and Testament (LWT)
    if (mqttClient.connect(DEVICE_ID, MQTT_USER, MQTT_PASS,
                           topicAvailability.c_str(), 1, true, "offline")) {
        Serial.println("[MQTT] Terhubung ke broker!");

        // 1. Publikasikan status online retained
        mqttClient.publish(topicAvailability.c_str(), "online", true);

        // 2. Langganan topik perintah kontrol
        mqttClient.subscribe(topicCmd.c_str(), 1);

        // 3. Publikasikan status awal ke broker
        publishState();
    } else {
        Serial.printf("[MQTT] Gagal terhubung, rc=%d. Akan mencoba lagi...\n", mqttClient.state());
    }
}

void handleMqttMessage(char* topic, byte* payload, unsigned int length) {
    char jsonBuffer[1024];
    if (length >= sizeof(jsonBuffer)) {
        Serial.println("[MQTT] Pesan terlalu besar untuk diproses.");
        return;
    }

    memcpy(jsonBuffer, payload, length);
    jsonBuffer[length] = '\0';

    JsonDocument doc;
    DeserializationError err = deserializeJson(doc, jsonBuffer);
    if (err) {
        Serial.println("[MQTT] Parsing JSON gagal.");
        return;
    }

    const char* cmdId = doc["id"] | "unknown";
    const char* channel = doc["channel"] | "";
    const char* action = doc["action"] | "set";
    bool val = doc["value"] | false;

    Serial.printf("[CMD] id: %s, channel: %s, action: %s, value: %s\n",
                  cmdId, channel, action, val ? "true" : "false");

    bool changed = false;

    if (strcmp(channel, "lamp_tengah") == 0) {
        stateLampTengah = (strcmp(action, "toggle") == 0) ? !stateLampTengah : val;
        changed = true;
    } else if (strcmp(channel, "lamp_dapur_tamu") == 0) {
        stateLampDapurTamu = (strcmp(action, "toggle") == 0) ? !stateLampDapurTamu : val;
        changed = true;
    } else if (strcmp(channel, "lamp_kamar") == 0) {
        stateLampKamar = (strcmp(action, "toggle") == 0) ? !stateLampKamar : val;
        changed = true;
    } else if (strcmp(channel, "relay_fan") == 0 || strcmp(channel, "relay") == 0) {
        stateRelay = (strcmp(action, "toggle") == 0) ? !stateRelay : val;
        changed = true;
    } else if (strcmp(channel, "buzzer") == 0) {
        stateBuzzer = (strcmp(action, "toggle") == 0) ? !stateBuzzer : val;
        changed = true;
    }

    if (changed) {
        updateHardwareOutputs();

        // 1. Kirim Ack perintah
        JsonDocument ackDoc;
        ackDoc["id"] = cmdId;
        ackDoc["status"] = "ok";
        ackDoc["channel"] = channel;
        char ackBuf[256];
        serializeJson(ackDoc, ackBuf);
        mqttClient.publish(topicAck.c_str(), ackBuf, false);

        // 2. Kirim update state ke broker
        publishState();
    }
}

void publishState() {
    if (!mqttClient.connected()) return;

    JsonDocument doc;
    JsonObject channels = doc["channels"].to<JsonObject>();
    channels["lamp_tengah"] = stateLampTengah;
    channels["lamp_dapur_tamu"] = stateLampDapurTamu;
    channels["lamp_kamar"] = stateLampKamar;
    channels["relay_fan"] = stateRelay;
    channels["buzzer"] = stateBuzzer;

    JsonObject sensors = doc["sensors"].to<JsonObject>();
    sensors["gas_raw"] = currentGasRaw;
    sensors["is_dark"] = currentIsDark;

    doc["ts"] = millis() / 1000;

    char buffer[512];
    serializeJson(doc, buffer);
    mqttClient.publish(topicState.c_str(), buffer, true);
}

void publishEvent(const char* eventName, const char* channel, float value) {
    if (!mqttClient.connected()) return;

    JsonDocument doc;
    doc["event"] = eventName;
    doc["channel"] = channel;
    doc["value"] = value;
    doc["threshold"] = GAS_RAW_THRESHOLD;
    doc["ts"] = millis() / 1000;

    char buffer[256];
    serializeJson(doc, buffer);
    mqttClient.publish(topicEvent.c_str(), buffer, false);
}
