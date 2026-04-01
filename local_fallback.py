import json
import os

DB_PATH = "objetos_db.json"
IGNORE_CLASSES = {"person", "people", "man", "woman", "hand", "hands", "personas"}

# 1. AJUSTE SEGÚN NORMATIVA COLOMBIA (Resolución 2184)
# Blanco: Plástico, vidrio, metales, papel, cartón (limpios).
# Verde: Restos de comida, desechos agrícolas (orgánicos).
# Negro: Papel higiénico, servilletas usadas, cartón contaminado, residuos COVID, jeringas.
COLOR_BY_TYPE = {
    "aprovechable": "blanco",
    "organico": "verde",
    "no_aprovechable": "negro",
    "desconocido": "negro",
}

TRANSLATIONS = {
    # --- aprovechable (Aprovechables) ---
    "bottle": "botella",
    "plastic bottle": "botella plastica",
    "glass bottle": "botella de vidrio",
    "can": "lata",
    "soda can": "lata de gaseosa",
    "glass": "vidrio",
    "wine glass": "copa de vidrio",
    "cup": "vaso",
    "plastic cup": "vaso plastico",
    "box": "caja",
    "paper": "papel",
    "cardboard": "carton",
    "newspaper": "periodico",
    "magazine": "revista",
    "bag": "bolsa",
    "plastic bag": "bolsa plastica",
    "plastic": "plastico",
    "metal": "metal",
    "container": "envase",
    "pot": "pote",
    "plastic pot": "pote plastico",
    "jar": "tarro",
    "shampoo bottle": "tarro de champu",
    "tetra pak": "tetra pak",
    "envelope": "sobre de papel",
    
    # --- VERDE (Orgánicos) ---
    "apple": "manzana",
    "banana": "banano",
    "vegetable": "vegetal",
    "food": "comida",
    "banana peel": "cascara de banano",
    "orange peel": "cascara de naranja",
    "coffee grounds": "cuncho de cafe",
    "eggshell": "cascara de huevo",
    "meat": "carne",
    "chicken bone": "hueso de pollo",
    "leaf": "hoja",
    "grass": "pasto",
    "orange": "naranja",
    "lettuce": "lechuga",
    "potato": "papa",
    "carrot": "zanahoria",
    "bread": "pan",
    "fruit": "fruta",
    
    # --- NEGRO (No aprovechables / Riesgo) ---
    "donut": "donut",
    "napkin": "servilleta",
    "toilet paper": "papel higienico",
    "tissue": "papel de toilette",
    "cigarette butt": "colilla de cigarro",
    "coffee cup": "taza de cafe", # Generalmente de cartón encerado/sucio
    "coffee filter": "filtro de cafe",
    "cigarette pack": "paquete de cigarros",
    "face mask": "tapabocas",
    "mask": "mascarilla",
    "syringe": "jeringa",
    "band-aid": "curita",
    "gloves": "guantes",
    "diaper": "panal",
    "styrofoam": "icopor",
    "chip bag": "paquete de papas", # Metalizado, no aprovechable fácilmente
    "candy wrapper": "envoltura de dulce",
    
    # Otros
    "umbrella": "sombrilla",
    "phone": "celular",
    "laptop": "portatil",
    "battery": "bateria",
    "oil": "aceite",
}

def ensure_db_exists():
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump({}, f)

def load_db():
    ensure_db_exists()
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def normalize_name(name: str) -> str:
    if not name:
        return ""
    value = name.lower().strip()
    return value.replace("_", " ").replace("-", " ")

def find_local_entry(class_name: str):
    try:
        db = load_db()
        name = normalize_name(class_name)
        if name in db:
            return db[name]

        for key, value in db.items():
            normalized_key = normalize_name(key)
            if normalized_key == name or normalized_key in name or name in normalized_key:
                return value
    except Exception:
        pass
    return None

def translate_object_name(class_name: str) -> str:
    name = normalize_name(class_name)
    return TRANSLATIONS.get(name, name)


def classify_type_by_object_name(object_name: str) -> str:
    name = normalize_name(object_name)

    aprovechables = {
        "botella", "lata", "vaso", "bolsa", "papel", "carton", "caja",
        "periodico", "revista", "envase", "frasco", "tarro", "plástico",
        "plastico", "metal", "lata de atun", "tarro de champu", "pote", 
        "tetra pak", "sobre de papel", "vidrio"
    }
    organicos = {
        "manzana", "banano", "banana", "vegetal", "comida", "restos fruta",
        "cascara", "cascara de banano", "cascara de naranja", "cascara de huevo",
        "carne", "hueso de pollo", "hoja", "pasto", "naranja", "lechuga",
        "papa", "zanahoria", "fruta", "pan"
    }
    no_aprovechables = {
        "donut", "servilleta", "papel higienico", "papel de toilette", "colilla de cigarro",
        "icopor", "tapon", "panual", "panal", "tapabocas", "mascarilla", "paquete de cigarros",
        "empaque", "envoltura", "carton sucio", "cigarrillo", "grasa", "jeringa", 
        "curita", "guantes", "taza de cafe", "paquete de papas"
    }

    if any(token in name for token in aprovechables):
        return "APROVECHABLE"
    if any(token in name for token in organicos):
        return "ORGANICO"
    if any(token in name for token in no_aprovechables):
        return "NO_APROVECHABLE"
    return "DESCONOCIDO"


def build_local_classification(yolo_objects):
    default_resp = {
        "tipo": "desconocido",
        "objeto": "desconocido",
        "color": "negro",
    }

    if not yolo_objects:
        return default_resp

    valid_objects = [
        obj for obj in yolo_objects
        if normalize_name(obj.get("class_name")) not in IGNORE_CLASSES
    ]

    if not valid_objects:
        return default_resp

    best = max(valid_objects, key=lambda obj: obj.get("confidence", 0))
    class_name = normalize_name(best.get("class_name", "desconocido"))
    local_entry = find_local_entry(class_name)

    if local_entry:
        objeto = local_entry.get("objeto", translate_object_name(class_name))
        tipo = local_entry.get("tipo") or classify_type_by_object_name(objeto)
        return {
            "tipo": tipo.upper(),
            "objeto": objeto,
            "color": COLOR_BY_TYPE.get(tipo.lower(), "negro"),
        }

    objeto = translate_object_name(class_name)
    tipo = classify_type_by_object_name(objeto)
    return {
        "tipo": tipo,
        "objeto": objeto,
        "color": COLOR_BY_TYPE.get(tipo.lower(), "negro"),
    }