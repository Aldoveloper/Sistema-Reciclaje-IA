#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>

// 🔐 WIFI
const char* ssid = "NIRVANA 2.4";
const char* password = "3232041158";

// 🌐 Servidor
const char* serverUrl = "http://192.168.1.126:8000/upload";

// 🔦 FLASH
#define FLASH_LED_PIN 4

// CONFIG CAMARA AI THINKER (Pines Estándar)
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

void setup() {
  // Serial para Debug
  Serial.begin(115200);
  
  // Serial2 para comunicación con Arduino Nano (RX=15, TX=14)
  // Nota: Conecta TX del Nano al pin 15 y RX del Nano al pin 14
  Serial2.begin(9600, SERIAL_8N1, 15, 14); 
  
  delay(1000);
  Serial.println("🚀 Iniciando sistema...");

  pinMode(FLASH_LED_PIN, OUTPUT);
  digitalWrite(FLASH_LED_PIN, LOW);

  // 📷 CONFIGURACIÓN CÁMARA
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  config.frame_size = FRAMESIZE_VGA;  // 640x480
  config.jpeg_quality = 10;
  config.fb_count = 2;

  if (esp_camera_init(&config) != ESP_OK) {
    Serial.println("❌ Error al iniciar cámara");
    return;
  }

  // 🔧 Ajustes de sensor para mejor imagen
  sensor_t * s = esp_camera_sensor_get();
  s->set_vflip(s, 1);
  s->set_hmirror(s, 1);
  s->set_whitebal(s, 1);
  s->set_exposure_ctrl(s, 1);
  s->set_gain_ctrl(s, 1);

  // 🌐 WIFI
  WiFi.begin(ssid, password);
  Serial.print("📡 Conectando WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ WiFi conectado");
  Serial.print("📍 IP: "); Serial.println(WiFi.localIP());
}

void loop() {
 
  // Escuchar orden del Arduino Nano
  if (Serial2.available()) {
    
    char c = Serial2.read();
     Serial.println("📸 hay serial2...");
    if (c == 'S') { // 'S' de Shoot
      Serial.println("📸 Orden recibida del Nano...");
      capturarYEnviar();
    }
  }
}

void capturarYEnviar() {
  // 🔥 WARMUP: Limpiar el buffer de la cámara
  for (int i = 0; i < 5; i++) {
    camera_fb_t * temp = esp_camera_fb_get();
    if (temp) esp_camera_fb_return(temp);
    delay(10);
  }

  // 🔦 FLASH ON (Opcional)
  digitalWrite(FLASH_LED_PIN, HIGH);
  delay(300);

  camera_fb_t * fb = esp_camera_fb_get();
  digitalWrite(FLASH_LED_PIN, LOW); // FLASH OFF

  if (!fb) {
    Serial.println("❌ Fallo en captura");
    return;
  }

  Serial.println("📤 Enviando al servidor...");
  HTTPClient http;
  http.begin(serverUrl);
  http.setTimeout(30000); // 15 seg para IA
  http.addHeader("Content-Type", "image/jpeg");

  int responseCode = http.POST(fb->buf, fb->len);

  if (responseCode > 0) {
    String payload = http.getString();
    Serial.println("🧠 Respuesta recibida.");
    
    // ENVIAR RESPUESTA AL NANO
    Serial2.println(payload); 
    Serial.println("📤 JSON reenviado al Nano");
  } else {
    Serial.print("❌ Error HTTP: ");
    Serial.println(http.errorToString(responseCode));
    Serial2.println("{\"error\": \"http_fail\"}"); // Avisar al Nano del fallo
  }

  http.end();
  esp_camera_fb_return(fb);
}