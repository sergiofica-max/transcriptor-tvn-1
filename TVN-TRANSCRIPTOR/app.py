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

# =====================================================
# CARPETAS
# =====================================================

os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)
os.makedirs("temp", exist_ok=True)
os.makedirs("output", exist_ok=True)
os.makedirs("logs", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

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
# (Whisper se agregará en el próximo capítulo)
# =====================================================

@app.post("/upload")
async def upload(file: UploadFile = File(...)):

    destino = os.path.join("temp", file.filename)

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
# EJECUCIÓN LOCAL
# =====================================================

if __name__ == "__main__":

    puerto = int(os.environ.get("PORT", 8000))

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=puerto,
        reload=True
    )
