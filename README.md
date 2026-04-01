# Sistema-Reciclaje-IA
#WEB: https://clasificacion-residuos-i-pynohfm.gamma.site/
# Video: https://drive.google.com/file/d/1tNur45p5tFHtMFAgUJMKZ-6zakxFMeYF/view?usp=sharing

---

# INFORME TÉCNICO: SISTEMA DE CLASIFICACIÓN DE RESIDUOS CON IA
**Documentación de Proyecto de Sistemas Embebidos y Visión Artificial**

## 1. INTRODUCCIÓN
El presente proyecto describe el desarrollo de un sistema automatizado para la gestión de residuos sólidos, alineado con la normativa de separación en la fuente de Colombia (Resolución 2184). El objetivo es crear una estación de reciclaje inteligente que, mediante visión artificial (YOLO) e Inteligencia Artificial Generativa (Gemini), identifique objetos y los deposite en el contenedor correspondiente (Blanco, Verde o Negro) a través de actuadores servomotores.

---

## 2. ARQUITECTURA DEL SISTEMA
El sistema se basa en una arquitectura distribuida de tres capas:

1.  **Capa de Percepción (Arduino Nano + Sensores):** Detecta la presencia física del objeto mediante un sensor ultrasónico.
2.  **Capa de Captura y Transmisión (ESP32-CAM):** Captura la imagen digital y la transmite vía HTTP a un servidor central.
3.  **Capa de Procesamiento (Backend Python):** Ejecuta modelos de Deep Learning (YOLOv11) y consultas a la API de Gemini para la clasificación lógica.



---

## 3. DOCUMENTACIÓN DEL FIRMWARE: ESP32-CAM
El firmware de la ESP32-CAM actúa como un puente entre el hardware de campo y la nube/servidor local.

### Funcionalidades Clave:
* **Comunicación Serial Dual:** Utiliza `Serial` para depuración y `Serial2` (Pines 15 RX, 14 TX) para recibir la orden de disparo ('S') del Nano.
* **Gestión de Cámara:** Configurada en formato JPEG, resolución VGA (640x480) y calidad 10 para optimizar el ancho de banda.
* **Protocolo HTTP:** Envía los bytes de la imagen mediante un método `POST` al servidor Python.
* **Manejo de Flash:** Activa el LED integrado (GPIO 4) brevemente durante la captura para garantizar iluminación en entornos cerrados.

### Parámetros de Conexión:
* **Baudrate Serial2:** 9600 bps.
* **Timeout HTTP:** 30 segundos (tolerancia para el procesamiento de IA).

---

## 4. DOCUMENTACIÓN DEL FIRMWARE: ARDUINO NANO
El Arduino Nano actúa como el controlador maestro de la estructura mecánica y la interfaz de usuario.

### Control de Actuadores y Sensores:
* **Sensor Ultrasónico (HC-SR04):** Monitorea constantemente la distancia. Al detectar un objeto a menos de **9 cm**, dispara el flujo de trabajo.
* **Servomotores (SG90):** Tres servos conectados a los pines 10, 11 y 12. Cada uno representa una compuerta:
    * **Blanco:** Aprovechables.
    * **Verde:** Orgánicos.
    * **Negro:** No aprovechables.
* **Pantalla LCD I2C:** Informa al usuario sobre el estado del sistema ("Procesando", "Tipo: Orgánico", etc.).

### Lógica de Comunicación:
Envía el caracter `'S'` al ESP32 y entra en un estado de espera (bloqueante controlado) hasta recibir una cadena JSON de respuesta o alcanzar un timeout.

---

## 5. DOCUMENTACIÓN DEL SCRIPT DE PYTHON (BACKEND)
El backend es el "cerebro" del sistema, encargado de la visión artificial pesada.

### Flujo de Procesamiento:
1.  **Detección YOLO (reconocer.py):** Utiliza un modelo `yolo11n.pt` para identificar objetos genéricos en la imagen (botellas, tazas, frutas).
2.  **Clasificación con Gemini (apiGemini.py):** Envía la imagen y los nombres de los objetos detectados por YOLO a la IA de Google para obtener una clasificación precisa según el contexto colombiano.
3.  **Sistema de Fallback (local_fallback.py):** Si la API de Gemini falla o no hay internet, el sistema usa una base de datos local JSON para clasificar el objeto basándose únicamente en la detección de YOLO.

### Integración:
El servidor (FastAPI) recibe la imagen, orquesta los tres scripts anteriores y devuelve al Arduino un JSON simplificado:
```json
{"objeto": "botella", "tipo": "APROVECHABLE", "color": "blanco"}
```

---

## 6. COMUNICACIÓN SERIAL Y NIVELES LÓGICOS
Un aspecto crítico del proyecto es la interconexión UART entre dispositivos con voltajes distintos.

### Manejo de Niveles Lógicos:
* **Arduino Nano:** Opera a **5V**.
* **ESP32-CAM:** Opera a **3.3V**.

**Conexión con Divisor de Voltaje:** Para proteger el pin RX (GPIO 15) del ESP32, se ha implementado un divisor de voltaje entre el TX del Nano y el RX del ESP32 utilizando resistencias de 1kΩ y 2kΩ, reduciendo los 5V a 3.3V seguros.



---

## 7. INSTRUCCIONES DE MONTAJE Y CONFIGURACIÓN

1.  **Hardware:**
    * Conectar el LCD I2C a los pines A4(SDA) y A5(SCL) del Nano.
    * Conectar los Servos a los pines 10, 11 y 12 del Nano (alimentación de 5V).
    * Realizar el divisor de voltaje para la línea TX del Nano -> RX del ESP32.
2.  **Software:**
    * Cargar el firmware al Nano mediante Arduino IDE.
    * Cargar el firmware al ESP32-CAM (requiere adaptador FTDI).
    * Ejecutar el servidor Python: `uvicorn server:app --host 0.0.0.0 --port 8000`.
    * Asegurarse de que el `serverUrl` en el código del ESP32 coincida con la IP de la computadora.

---
