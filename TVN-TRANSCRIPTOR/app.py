from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import os
import uuid

APP_NAME = "24 Horas | Transcriptor IA"
VERSION = "1.0"

app = FastAPI(title=APP_NAME, version=VERSION)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Asegurar directorios físicos básicos
os.makedirs(os.path.join(BASE_DIR, "static"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "templates"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "temp"), exist_ok=True)

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Diccionarios para el control de archivos
TAREAS_PENDIENTES = {}
TAREAS_PROCESADAS = {}

# 1. RUTA PRINCIPAL (Frontend)
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"titulo": APP_NAME}
    )

# 2. SUBIDA DE ARCHIVOS MULTIMEDIA
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    task_id = str(uuid.uuid4())
    nombre_archivo = f"{task_id}_{file.filename}"
    destino = os.path.join(BASE_DIR, "temp", nombre_archivo)
    
    with open(destino, "wb") as f:
        f.write(await file.read())
    
    # Lo dejamos listo para que el motor lo consuma
    TAREAS_PENDIENTES[task_id] = {
        "id": task_id,
        "nombre": file.filename,
        "ruta_local": destino,
        "estado": "pendiente",
        "texto": ""
    }
    
    return JSONResponse({"ok": True, "task_id": task_id, "mensaje": "Audio en cola."})

# 3. CONSULTA DE ESTADO DE LA WEB
@app.get("/api/status/{task_id}")
async def check_status(task_id: str):
    if task_id in TAREAS_PROCESADAS:
        return {"estado": "completado", "texto": TAREAS_PROCESADAS[task_id]["texto"]}
    if task_id in TAREAS_PENDIENTES:
        return {"estado": TAREAS_PENDIENTES[task_id]["estado"], "texto": TAREAS_PENDIENTES[task_id]["texto"]}
    return {"estado": "no_existe"}

if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=puerto, reload=False)
