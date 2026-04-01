from fastapi import FastAPI, Request
import os

from procesar_imagen import procesar_imagen, UPLOAD_DIR

app = FastAPI()


@app.post("/upload")
async def upload(request: Request):
    image_bytes = await request.body()

    # Nombre fijo, siempre reemplaza la imagen anterior
    filename = "latest.jpg"
    filepath = os.path.join(UPLOAD_DIR, filename)

    # 💾 Guardar/ Reemplazar imagen
    with open(filepath, "wb") as f:
        f.write(image_bytes)

    print(f"📸 Imagen guardada / reemplazada: {filepath}")

    # Procesar inmediatamente y devolver resultado
    resultado = procesar_imagen(image_bytes, filename)

    if resultado.get("gemini") is not None:
        return resultado.get("gemini")
    
    
   # return {
    #    "status": "ok",
     #   "file": filename,
      #  "yolo_objects": resultado.get("yolo_objects"),
       # "gemini": resultado.get("gemini"),
        #"used_local_fallback": resultado.get("used_local_fallback", False),
        #"local_fallback": resultado.get("local_fallback"),
        #"error": resultado.get("error"),
    #}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
