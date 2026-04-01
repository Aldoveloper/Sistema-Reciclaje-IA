#include <Wire.h> 
#include <LiquidCrystal_I2C.h>
#include <Servo.h>
#include <SoftwareSerial.h>
#include <ArduinoJson.h>

// 1. CONFIGURACIÓN DE HARDWARE
LiquidCrystal_I2C lcd(0x27, 16, 2);
SoftwareSerial espSerial(2, 3); // RX=2, TX=3

Servo servoBlanco, servoVerde, servoNegro;

const int trigPin = 8;
const int echoPin = 9;

// BAJAMOS EL UMBRAL A 12cm (Basado en tu código de prueba que usa 10cm)
const int umbral = 9; 

bool esperandoRespuesta = false;

void setup() {
  Serial.begin(9600);
  espSerial.begin(9600);
  
  lcd.init();
  lcd.backlight();
  mostrarMensajeLCD("SISTEMA IA", "INICIANDO...");
  
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  servoBlanco.attach(10);
  servoVerde.attach(11);
  servoNegro.attach(12);
  
  posicionInicial();
  delay(2000); 

  mostrarMensajeLCD("SISTEMA LISTO", "ESPERANDO OBJETO");
}

void loop() {
  if (!esperandoRespuesta) {
    int distancia = obtenerDistancia();

    // LÓGICA DEL CÓDIGO BASE: Simple y directa. 
    // Usamos > 0 y <= umbral (12cm) para evitar detectar las paredes de la estructura
    if (distancia > 5 && distancia <= umbral) {
      esperandoRespuesta = true; 

      mostrarMensajeLCD("OBJETO DETECTADO", "TOMANDO FOTO...");
      Serial.print(F("\n🎯 Objeto detectado a "));
      Serial.print(distancia);
      Serial.println(F("cm! Enviando 'S'..."));
      
      // Limpieza de buffer antes de enviar la señal
      while(espSerial.available()) espSerial.read(); 
      espSerial.print('S'); 

      mostrarMensajeLCD("ENVIANDO A IA", "PROCESANDO...");

      unsigned long inicioEspera = millis();
      String jsonRespuesta = "";
      bool lecturaCompleta = false;

      // Timeout de 20 segundos para la respuesta del servidor
      while (millis() - inicioEspera < 35000) {
        if (espSerial.available()) {
          char c = espSerial.read();
          Serial.print(c); // Monitoreo en PC
          
          if (c == '{' || jsonRespuesta.length() > 0) {
            jsonRespuesta += c;
            if (c == '}') { 
              lecturaCompleta = true;
              break; 
            }
          }
        }
      }

      Serial.println(); 

      if (lecturaCompleta) {
        procesarRespuesta(jsonRespuesta);
        delay(5000); // Pausa para leer el resultado en el LCD
      } else {
        mostrarMensajeLCD("ERROR:", "SIN RESPUESTA");
        delay(3000);
      }

      mostrarMensajeLCD("RESETEANDO...", "LISTO EN 2 SEG");
      posicionInicial();
      delay(2000); 
      
      esperandoRespuesta = false; 
      mostrarMensajeLCD("SISTEMA LISTO", "ESPERANDO OBJETO");
    }
  }
  
  // CRÍTICO: Mantenemos el delay de 100ms igual que en tu código base 
  // para darle tiempo al sonido de disiparse y evitar colisiones de eco.
  delay(100); 
}

// --- FUNCIONES TÉCNICAS ---

int obtenerDistancia() {
  digitalWrite(trigPin, LOW); delayMicroseconds(2);
  digitalWrite(trigPin, HIGH); delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  
  // Timeout de 30000 microsegundos para evitar que el Arduino se congele
  long duracion = pulseIn(echoPin, HIGH, 30000);
  
  if (duracion == 0) return 999; // Retorna 999 si no detecta nada a tiempo
  
  // El cálculo trunca automáticamente los decimales a entero, 
  // eliminando el micro-ruido que veíamos de 0.51cm
  return duracion * 0.034 / 2;
}

void procesarRespuesta(String json) {
  // 1. Crear el documento para el JSON que llega (un solo nivel)
  StaticJsonDocument<500> doc; 
  DeserializationError error = deserializeJson(doc, json);

  if (error) {
    mostrarMensajeLCD("ERROR JSON", "CORRUPTO");
    Serial.print(F("Fallo deserialización: "));
    Serial.println(error.f_str());
    return;
  }

  // 2. Extraer los datos DIRECTAMENTE del objeto principal
  // Ya no usamos doc[0] porque la ESP32 envía el objeto directo
  String tipo = doc["tipo"] | "??";
  String objeto = doc["objeto"] | "desconocido";
  
  tipo.toUpperCase();
  
  // --- ACTUALIZACIÓN DEL LCD ---
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("TIPO: " + tipo);
  lcd.setCursor(0, 1);
  
  // Mostramos el nombre del objeto (máximo 16 caracteres para el LCD)
  if (objeto.length() > 16) {
    lcd.print(objeto.substring(0, 16));
  } else {
    lcd.print(objeto);
  }

  // --- CONTROL DE ACTUADORES ---
  // Ajustamos los nombres para que coincidan con lo que envía tu IA
  if (tipo == "BLANCO" || tipo == "APROVECHABLE" || tipo == "papel") {
    moverServo(servoBlanco);
  } else if (tipo == "VERDE" || tipo == "ORGANICO") {
    moverServo(servoVerde);
  } else if (tipo == "NEGRO" || tipo == "NO_APROVECHABLE" || tipo == "DESCONOCIDO") {
    moverServo(servoNegro);
  }
  
  Serial.println("Acción completada para: " + tipo);
}

void moverServo(Servo &s) {
  s.write(90);  
  delay(4000);  
  s.write(0);   
}

void posicionInicial() {
  servoBlanco.write(0);
  servoVerde.write(0);
  servoNegro.write(0);
}

void mostrarMensajeLCD(String l1, String l2) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(l1);
  lcd.setCursor(0, 1);
  lcd.print(l2);
}