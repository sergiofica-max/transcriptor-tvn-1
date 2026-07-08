from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import os

# =====================================================
# CONFIGURACIÓN
# =====================================================
APP_NAME = "24 Horas | Transcriptor IA"
VERSION = "1.0"

app = FastAPI(
    title=APP_NAME,
    version=VERSION,
    description="Sistema profesional de transcripción para el Departamento de Prensa"
)

# Obtener la ruta absoluta del directorio actual para evitar pérdidas en Linux/Railway
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# =====================================================
# CARPETAS DE EMERGENCIA (Asegurar entorno)
# =====================================================
os.makedirs(os.path.join(BASE_DIR, "static"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "templates"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "temp"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "output"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)

# Crear un archivo index.html de respaldo SOLO si la carpeta quedó completamente vacía
RUTA_INDEX = os.path.join(BASE_DIR, "templates", "index.html")
if not os.path.exists(RUTA_INDEX):
    with open(RUTA_INDEX, "w", encoding="utf-8") as f:
        f.write("<h1>Servidor Online - Sube tu index.html real a la carpeta templates de GitHub</h1>")

# =====================================================
# CONFIGURAR MONTAJES CON RUTAS ABSOLUTAS
# =====================================================
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# =====================================================
# PÁGINA PRINCIPAL
# =====================================================
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "titulo": APP_NAME
        }
    )

# =====================================================
# ESTADO DEL SERVIDOR
# =====================================================
@app.get("/health")
async def health():
    return {
        "status": "online",
        "version": VERSION
    }

# =====================================================
# SUBIDA DE ARCHIVOS
# =====================================================
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    destino = os.path.join(BASE_DIR, "temp", file.filename)
    with open(destino, "wb") as f:
        f.write(await file.read())
    
    return JSONResponse(
        {
            "ok": True,
            "archivo": file.filename,
            "mensaje": "Archivo recibido correctamente."
        }
    )

# =====================================================
# EJECUCIÓN
# =====================================================
if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 8080))
    uvicorn.run("app:app", host="0.0.0.0", port=puerto, reload=False)
