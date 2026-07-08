from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import uuid

APP_NAME = "24 Horas | Transcriptor IA"
VERSION = "1.0"

app = FastAPI(title=APP_NAME, version=VERSION)

# Habilitar CORS obligatorio para que Colab no sea rebotado por seguridad
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Asegurar directorios físicos en Railway
os.makedirs(os.path.join(BASE_DIR, "static"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "templates"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "temp"), exist_ok=True)

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Diccionarios en memoria para conectar la web con Colab
TAREAS_PENDIENTES = {}
TAREAS_PROCESADAS = {}

class WebhookResultado(BaseModel):
    task_id: str
    texto: str

# 1. ENTRADA DE LA PÁGINA WEB
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"titulo": APP_NAME}
    )

# 2. SUBIDA DESDE EL NAVEGADOR
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    task_id = str(uuid.uuid4())
    nombre_archivo = f"{task_id}_{file.filename}"
    destino = os.path.join(BASE_DIR, "temp", nombre_archivo)
    
    with open(destino, "wb") as f:
        f.write(await file.read())
    
    TAREAS_PENDIENTES[task_id] = {
        "id": task_id,
        "nombre": file.filename,
        "ruta_local": destino,
        "estado": "pendiente",
        "texto": ""
    }
    
    return JSONResponse({"ok": True, "task_id": task_id, "mensaje": "Audio en cola."})

# 3. COLAB LLAMA AQUÍ PARA RECOGER LA TAREA
@app.get("/api/worker/next")
async def get_next_task():
    for task_id, info in TAREAS_PENDIENTES.items():
        if info["estado"] == "pendiente":
            info["estado"] = "procesando"
            return {"hay_tarea": True, "task_id": task_id, "nombre": info["nombre"]}
    return {"hay_tarea": False}

# 4. COLAB LLAMA AQUÍ PARA DESCARGAR EL VIDEO FÍSICO
from fastapi.responses import FileResponse
@app.get("/api/worker/download/{task_id}")
async def download_file(task_id: str):
    if task_id in TAREAS_PENDIENTES:
        return FileResponse(TAREAS_PENDIENTES[task_id]["ruta_local"])
    return JSONResponse({"error": "No encontrado"}, status_code=404)

# 5. COLAB LLAMA AQUÍ PARA INYECTAR EL TEXTO TRANSCRITO
@app.post("/api/worker/webhook")
async def recibir_transcripcion(data: WebhookResultado):
    if data.task_id in TAREAS_PENDIENTES:
        info = TAREAS_PENDIENTES.pop(data.task_id)
        TAREAS_PROCESADAS[data.task_id] = {
            "nombre": info["nombre"],
            "texto": data.texto
        }
        # Eliminar el archivo de video temporal para no llenar el disco de Railway
        if os.path.exists(info["ruta_local"]):
            os.remove(info["ruta_local"])
        return {"ok": True}
    return JSONResponse({"error": "ID inválido"}, status_code=400)

# 6. LA WEB LLAMA AQUÍ CADA 3 SEGUNDOS PARA ACTUALIZAR LA PANTALLA
@app.get("/api/status/{task_id}")
async def check_status(task_id: str):
    if task_id in TAREAS_PROCESADAS:
        return {"estado": "completado", "texto": TAREAS_PROCESADAS[task_id]["texto"]}
    if task_id in TAREAS_PENDIENTES:
        return {"estado": TAREAS_PENDIENTES[task_id]["estado"], "texto": ""}
    return {"estado": "no_existe"}

if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=puerto, reload=False)
