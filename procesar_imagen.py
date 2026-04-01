import json
import os

from reconocer import analizar_imagen
from apiGemini import clasificar_basura_gemini
from local_fallback import build_local_classification

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def procesar_imagen(image_bytes, filename):
    try:
        filepath = os.path.join(UPLOAD_DIR, filename)

        yolo_resultados = analizar_imagen(filepath)

        # Guardar formato crudo y solo objetos en JSON
        raw_path = os.path.join(UPLOAD_DIR, "latest_yolo_raw.json")
        objects_path = os.path.join(UPLOAD_DIR, "latest_yolo_objects.json")

        if yolo_resultados is not None:
            if "raw" in yolo_resultados:
                try:
                    with open(raw_path, "w", encoding="utf-8") as json_f:
                        json.dump(yolo_resultados["raw"], json_f, ensure_ascii=False, indent=2)
                except Exception:
                    pass

            if "objects" in yolo_resultados:
                try:
                    with open(objects_path, "w", encoding="utf-8") as json_f:
                        json.dump(yolo_resultados["objects"], json_f, ensure_ascii=False, indent=2)
                except Exception:
                    pass

        yolo_objects = yolo_resultados.get("objects", []) if yolo_resultados else []
        local_fallback = build_local_classification(yolo_objects)

        if yolo_objects:
            object_labels = [
                f"{obj.get('class_name', 'desconocido')} ({obj.get('confidence', 0):.2f})"
                for obj in yolo_objects
            ]
            print("✅ YOLO reconoció:", ", ".join(object_labels))
        else:
            print("⚠️ No se detectaron objetos con YOLO; se envía la imagen a Gemini para clasificación final.")

        # Llamar a Gemini y usar fallback local si falla o devuelve desconocido
        raw_gemini_response = clasificar_basura_gemini(image_bytes, yolo_objects)
        used_local_fallback = False
        gemini_response = None

        if raw_gemini_response is None:
            used_local_fallback = True
            gemini_response = local_fallback
            print("⚠️ Gemini no respondió, usando fallback local.")
        else:
            try:
                parsed = json.loads(raw_gemini_response)
                if (
                    parsed.get("tipo") == "desconocido"
                    and parsed.get("objeto") == "desconocido"
                    and yolo_objects
                ):
                    used_local_fallback = True
                    gemini_response = local_fallback
                    print("⚠️ Gemini devolvió desconocido, usando fallback local basado en YOLO.")
                else:
                    gemini_response = parsed
            except Exception:
                used_local_fallback = True
                gemini_response = local_fallback
                print("⚠️ Respuesta de Gemini no pudo parsearse, usando fallback local.")

        fallback_path = os.path.join(UPLOAD_DIR, "latest_local_fallback.json")
        try:
            with open(fallback_path, "w", encoding="utf-8") as json_f:
                json.dump(gemini_response, json_f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        print(f"🧠 Respuesta final: {gemini_response}")

        return {
            "yolo_objects": yolo_objects,
            "gemini": gemini_response,
            "local_fallback": local_fallback,
            "used_local_fallback": used_local_fallback,
        }

    except Exception as e:
        print("❌ Error en procesar_imagen:", e)
        return {
            "error": str(e),
            "yolo_objects": [],
            "gemini": None,
        }
