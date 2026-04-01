import os
import time
import json
import threading
from google import genai
from google.genai import types

# Configuración de API
api_key = os.environ.get("GEMINI_API_KEY")
key_file = "gemini_api_key.txt"
if not api_key and os.path.exists(key_file):
    try:
        with open(key_file, "r", encoding="utf-8") as f:
            api_key = f.read().strip()
    except Exception as exc:
        print(f"⚠️ No se pudo leer {key_file}: {exc}")

if api_key:
    client = genai.Client(api_key=api_key)
else:
    print("❌ No se encontró clave Gemini. Crea gemini_api_key.txt con tu API key o define GEMINI_API_KEY.")
    client = None


def clasificar_basura_gemini(image_bytes, detected_objects):
    if client is None:
        print("❌ No hay cliente Gemini disponible. No se intentará la llamada a Gemini.")
        return None
    # Prompt optimizado para COLOMBIA y compatibilidad con tu Arduino Nano
    prompt = f"""
    Objetos detectados por YOLO: {detected_objects}.
    
    Instrucciones de Clasificación (Normativa Colombia):
    1. BLANCO (aprovechable): Botellas, plástico limpio, vidrio, latas, metal, papel, cartón.
    2. VERDE (organico): Restos de comida, cáscaras, desechos agrícolas.
    3. NEGRO (no_aprovechable): Servilletas usadas, papel higiénico, tapabocas, jeringas, cartón contaminado.

    Requerimientos:
    - Identifica el objeto principal.
    - Ignora humanos y manos.
    - Si no hay objetos en la lista de YOLO, identifícalo visualmente.
    """

    # Forzamos a Gemini a usar un esquema JSON estricto
    config = {
        "response_mime_type": "application/json",
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "objeto": {"type": "STRING"},
                "tipo": {"type": "STRING"},
                "color": {"type": "STRING"},
            },
            "required": ["objeto", "tipo", "color"],
        },
    }

    fallback_models = [
        "gemini-3-flash-preview",  # El más rápido actualmente
        "gemini-3.1-flash-lite-preview",
    ]

    timeout_seconds = 8.0  # Aumentado un poco por latencia de red
    deadline = time.time() + timeout_seconds

    def call_model(model_name, container):
        try:
            print(f"⏳ Intentando Gemini con modelo {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                    prompt,
                ],
                config=config,  # Aplicamos la configuración JSON
            )
            container["text"] = response.text
        except Exception as e:
            container["error"] = str(e)

    for model_name in fallback_models:
        remaining = deadline - time.time()
        if remaining <= 0:
            print("⚠️ Se acabó el tiempo de espera antes de intentar más modelos.")
            break

        print(f"🔧 Quedan {remaining:.1f}s para el intento con {model_name}.")
        result = {}
        thread = threading.Thread(
            target=call_model, args=(model_name, result), daemon=True
        )
        thread.start()
        thread.join(remaining)

        if "text" in result:
            print(f"✅ Gemini respondió con texto usando {model_name}.")
            try:
                data = json.loads(result["text"])
                tipo = data["tipo"].lower()
                if "aprovechable" in tipo or "blanco" in tipo:
                    data["tipo"] = "APROVECHABLE"
                    data["color"] = "blanco"
                elif "organico" in tipo or "verde" in tipo:
                    data["tipo"] = "ORGANICO"
                    data["color"] = "verde"
                else:
                    data["tipo"] = "NO_APROVECHABLE"
                    data["color"] = "negro"

                return json.dumps(data)
            except Exception as parse_error:
                print(f"⚠️ No se pudo parsear JSON de Gemini: {parse_error}")
                print(f"Respuesta cruda de Gemini: {result['text']}")
                continue

        if "error" in result:
            print(f"❌ Error de Gemini con {model_name}: {result['error']}")
        else:
            print(f"❌ No hubo respuesta de texto de Gemini para {model_name}.")

    print("❌ Fallo total de Gemini.")
    return None
