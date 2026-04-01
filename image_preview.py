import os

from PIL import Image, ImageDraw, ImageFont


def _load_font(image_width: int):
    size = max(18, image_width // 40)
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


def _measure_text(draw, text: str, font):
    if hasattr(draw, "textbbox"):
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    return font.getsize(text)


def annotate_image(image_path: str, yolo_objects=None, classification=None, output_path=None):
    if yolo_objects is None:
        yolo_objects = []
    if classification is None:
        classification = {}

    with Image.open(image_path) as image:
        image = image.convert("RGB")
        draw = ImageDraw.Draw(image)
        font = _load_font(image.width)

        for obj in yolo_objects:
            bbox = obj.get("bbox")
            if not bbox or len(bbox) != 4:
                continue

            x1, y1, x2, y2 = [float(coord) for coord in bbox]
            draw.rectangle([x1, y1, x2, y2], outline=(255, 165, 0), width=3)

            label = obj.get("class_name", "desconocido")
            confidence = obj.get("confidence")
            if confidence is not None:
                label = f"{label} {confidence:.2f}"

            text_width, text_height = _measure_text(draw, label, font)
            draw.rectangle([x1, y1 - text_height - 8, x1 + text_width + 10, y1], fill=(0, 0, 0, 180))
            draw.text((x1 + 5, y1 - text_height - 4), label, font=font, fill="white")

        if classification:
            lines = []
            if classification.get("objeto"):
                lines.append(f"Objeto: {classification['objeto']}")
            if classification.get("tipo"):
                lines.append(f"Tipo: {classification['tipo']}")
            if classification.get("color"):
                lines.append(f"Color: {classification['color']}")

            if lines:
                text = " | ".join(lines)
                text_width, text_height = _measure_text(draw, text, font)
                padding = 10
                draw.rectangle([10, 10, 10 + text_width + padding * 2, 10 + text_height + padding * 2], fill=(0, 0, 0, 180))
                draw.text((10 + padding, 10 + padding), text, font=font, fill="white")

        if output_path is None:
            project_root = os.path.dirname(os.path.abspath(__file__))
            output_path = os.path.join(project_root, "uploads", "latest_preview.jpg")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        image.save(output_path, quality=90)
        return output_path


if __name__ == "__main__":
    sample_objects = [
        {"bbox": [50, 100, 300, 400], "class_name": "apple", "confidence": 0.77},
    ]
    sample_classification = {"objeto": "manzana", "tipo": "ORGANICO", "color": "verde"}
    output = annotate_image("uploads/latest.jpg", yolo_objects=sample_objects, classification=sample_classification)
    print(f"Imagen anotada guardada en: {output}")
