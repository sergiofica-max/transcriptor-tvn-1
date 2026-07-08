from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
import os
import uuid

APP_NAME = "24 Horas | Transcriptor IA"
VERSION = "1.0"

app = FastAPI(title=APP_NAME, version=VERSION)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Asegurar creación de carpetas físicas
os.makedirs(os.path.join(BASE_DIR, "static"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "templates"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "temp"), exist_ok=True)

# Crear un archivo de respaldo ultra-básico por si Jinja2 falla
RUTA_INDEX = os.path.join(BASE_DIR, "templates", "index.html")
if not os.path.exists(RUTA_INDEX):
    with open(RUTA_INDEX, "w", encoding="utf-8") as f:
        f.write("<h1>Servidor base activo - Falta index.html real</h1>")

# Variables globales para el montaje seguro
templates = None
error_inicializacion = None

# Intentar montar las carpetas. Si falla, guardamos el error en lugar de congelar el servidor.
try:
    app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
    templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
except Exception as e:
    error_inicializacion = f"Error crítico al montar estáticos/plantillas: {str(e)}"

# Cola de tareas temporal
TAREAS_PENDIENTES = {}
TAREAS_PROCESADAS = {}

class WebhookResultado(BaseModel):
    task_id: str
    texto: str

# =====================================================
# PÁGINA PRINCIPAL CAPTURADORA DE ERRORES
# =====================================================
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Si hubo un error al encender el servidor, muéstralo de inmediato
    if error_inicializacion:
        return f"<div style='color:red; font-family:sans-serif; padding:20px;'><h2>🚨 Error de Inicialización en Railway:</h2><pre>{error_inicializacion}</pre></div>"
    
    try:
        # Intento de renderizado moderno
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"titulo": APP_NAME}
        )
    except Exception as e:
        # Si Jinja2 falla al renderizar el index.html, te dirá EXACTAMENTE por qué aquí mismo
        return f"""
        <div style="font-family:sans-serif; padding:30px; background:#fff5f5; border-left:5px solid #e53e3e;">
            <h2 style="color:#c53030; margin-top:0;">🚨 Error de Renderizado en tu Frontend (Jinja2)</h2>
            <p><strong>Detalle del error:</strong> <code>{str(e)}</code></p>
            <p><strong>Ruta donde Python está buscando el archivo:</strong> <code>{RUTA_INDEX}</code></p>
            <p><strong>¿El archivo index.html existe físicamente?:</strong> <code>{"SÍ" if os.path.exists(RUTA_INDEX) else "NO"}</code></p>
            <hr style="border:0; border-top:1px solid #fed7d7; margin:20px 0;">
            <p style="font-size:14px; color:#4a5568;">Revisa si en GitHub tu index.html se encuentra realmente guardado dentro de la carpeta <em>templates</em>.</p>
        </div>
        """

# =====================================================
# ENDPOINTS RESTANTES (Mantener compatibilidad)
# =====================================================
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    task_id = str(uuid.uuid4())
    destino = os.path.join(BASE_DIR, "temp", f"{task_id}_{file.filename}")
    with open(destino, "wb") as f:
        f.write(await file.read())
    TAREAS_PENDIENTES[task_id] = {"id": task_id, "nombre": file.filename, "ruta_local": destino, "estado": "pendiente"}
    return JSONResponse({"ok": True, "task_id": task_id})

@app.get("/api/worker/next")
async def get_next_task():
    for task_id, info in TAREAS_PENDIENTES.items():
        if info["estado"] == "pendiente":
            info["estado"] = "procesando"
            return {"hay_tarea": True, "task_id": task_id, "nombre": info["nombre"]}
    return {"hay_tarea": False}

@app.get("/health")
async def health():
    return {"status": "online", "error_inicial": error_inicializacion}

if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=puerto, reload=False)
