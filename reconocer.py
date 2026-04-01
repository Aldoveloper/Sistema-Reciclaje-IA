from ultralytics import YOLO
import os

# Carga un modelo YOLO11n pre-entrenado (asegúrate de tener yolo11n.pt disponible)
model = YOLO("yolo11n.pt")


def analizar_imagen(filepath: str):
    """Analiza la imagen con YOLO11 y muestra resultados."""
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"No se encontró el archivo: {filepath}")

    try:
        results = model(filepath)


        # Intenta obtener el JSON crudo de la respuesta
        raw_result = None
        if hasattr(results, "tojson"):
            raw_result = results.tojson()
        elif hasattr(results, "to_dict"):
            raw_result = results.to_dict()
        elif hasattr(results, "pandas"):
            raw_result = results.pandas().xyxy
        else:
            raw_result = [r.boxes.data.tolist() if hasattr(r, "boxes") else {} for r in results]

        # Extraer solo los objetos detectados con sus clases y confidencias
        objects = []
        for r in results:
            class_names = getattr(r, "names", None)
            if class_names is None and hasattr(results, "names"):
                class_names = results.names

            for box in getattr(r, "boxes", []):
                cls_id = int(box.cls[0]) if hasattr(box, "cls") else None
                conf = float(box.conf[0]) if hasattr(box, "conf") else None
                xyxy = box.xyxy[0].tolist() if hasattr(box, "xyxy") else None
                class_name = None
                if cls_id is not None:
                    if isinstance(class_names, dict):
                        class_name = class_names.get(cls_id)
                    elif isinstance(class_names, list) and cls_id < len(class_names):
                        class_name = class_names[cls_id]

                objects.append({
                    "class_id": cls_id,
                    "class_name": class_name,
                    "confidence": conf,
                    "bbox": xyxy,
                })

        return {
            "results": results,
            "raw": raw_result,
            "objects": objects,
        }

    except Exception as e:
        print("❌ Error en YOLO11:", e)
        return None
