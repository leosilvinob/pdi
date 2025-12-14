#include "esp_camera.h"
#include <WiFi.h>
#include <FS.h>
#include <SD.h>

//
// Based on ESP32 CameraWebServer example.
// This sketch is the base to re-add custom HTTP /cadastrar, SD persistence, and periodic recognition.
//

// ===================
// Select camera model
// ===================
#define CAMERA_MODEL_XIAO_ESP32S3 // Has PSRAM
#include "camera_pins.h"

// ===========================
// WiFi credentials
// ===========================
const char *ssid     = "lsb5";
const char *password = "12345678b";
const int SD_CS_PIN  = 21;
bool sd_ok_global    = false;

void startCameraServer();
void setupLedFlash(int pin);
void faces_set_sd_ready(bool ok);
void faces_load_db();
void faces_load_metadata();
int faces_periodic_recognize();
const char* faces_get_name(int id);
const char* faces_get_vinc(const char *name);
void faces_publish_result(int id, const char *name, const char *vinc);
void faces_set_status(const char *status);

void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  delay(4000);
  Serial.println();

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0       = Y2_GPIO_NUM;
  config.pin_d1       = Y3_GPIO_NUM;
  config.pin_d2       = Y4_GPIO_NUM;
  config.pin_d3       = Y5_GPIO_NUM;
  config.pin_d4       = Y6_GPIO_NUM;
  config.pin_d5       = Y7_GPIO_NUM;
  config.pin_d6       = Y8_GPIO_NUM;
  config.pin_d7       = Y9_GPIO_NUM;
  config.pin_xclk     = XCLK_GPIO_NUM;
  config.pin_pclk     = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM;
  config.pin_href     = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn     = PWDN_GPIO_NUM;
  config.pin_reset    = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.frame_size   = FRAMESIZE_240X240; // required for face recognition
  config.pixel_format = PIXFORMAT_JPEG;    // camera driver will decode internally for face rec
  config.grab_mode    = CAMERA_GRAB_WHEN_EMPTY;
  config.fb_location  = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = 10; // higher quality to avoid tiny/corrupted frames
  config.fb_count     = 2;  // double buffer for stability

  // camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x\n", err);
    return;
  }

  sensor_t *s = esp_camera_sensor_get();
  if (s->id.PID == OV3660_PID) {
    s->set_vflip(s, 1);
    s->set_brightness(s, 1);
    s->set_saturation(s, -2);
  }

  // Ensure 240x240 for face rec
  s->set_framesize(s, FRAMESIZE_240X240);

#if defined(CAMERA_MODEL_M5STACK_WIDE) || defined(CAMERA_MODEL_M5STACK_ESP32CAM)
  s->set_vflip(s, 1);
  s->set_hmirror(s, 1);
#endif

#if defined(CAMERA_MODEL_ESP32S3_EYE)
  s->set_vflip(s, 1);
#endif

#if defined(LED_GPIO_NUM)
  setupLedFlash(LED_GPIO_NUM);
#endif

  // SD init (lower speed for stability)
  sd_ok_global = SD.begin(SD_CS_PIN, SPI, 20000000U);
  faces_set_sd_ready(sd_ok_global);
  if (sd_ok_global) {
    if (!SD.exists("/faces")) {
      SD.mkdir("/faces");
    }
    faces_load_db();
    faces_load_metadata();
  } else {
    Serial.println("SD init failed (continuing without SD)");
  }

  WiFi.begin(ssid, password);
  WiFi.setSleep(false);

  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("WiFi connected, IP: ");
  Serial.println(WiFi.localIP());

  startCameraServer();
  Serial.printf("Camera Ready! Use 'http://%s' to connect\n", WiFi.localIP().toString().c_str());
}

void loop() {
  static unsigned long lastRecog = 0;
  const unsigned long INTERVAL = 3000;

  if (millis() - lastRecog > INTERVAL) {
    lastRecog = millis();
    int id = faces_periodic_recognize();
    if (id >= 0) {
        const char *name = faces_get_name(id);
        const char *vinc = faces_get_vinc(name);
        if (!name || !name[0]) name = "Unknown";
        if (!vinc || !vinc[0]) vinc = "Unknown";
        Serial.printf("Found: %s - %s (ID %d)\n", name, vinc, id);
        faces_publish_result(id, name, vinc);
    } else {
        faces_set_status("Nenhum rosto reconhecido.");
    }
  }

  delay(50);
}
