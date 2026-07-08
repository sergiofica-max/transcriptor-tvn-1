import whisper
import torch
import re
import gc
import time
import requests
import os

# URL DE TU SERVIDOR EN LIVE (RAILWAY)
API_URL = "https://transcriptor-tvn-1-production.up.railway.app"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🤖 Cargando motor Whisper oficial en modo: {DEVICE}...")

# Cargar el modelo base o large según lo que requieras de tu copia de librispeech
model = whisper.load_model("base", device=DEVICE)

def quitar_bucles_redundantes(texto):
    palabras = texto.split()
    if not palabras: return ""
    i, resultado, n = 0, [], len(palabras)
    while i < n:
        bucle_detectado = False
        for k in range(1, 16):
            if i + 2 * k <= n:
                chunk1 = palabras[i : i + k]
                chunk2 = palabras[i + k : i + 2 * k]
                c1_norm = [re.sub(r'[^\w]', '', w.lower()) for w in chunk1]
                c2_norm = [re.sub(r'[^\w]', '', w.lower()) for w in chunk2]
                if c1_norm == c2_norm and "".join(c1_norm) != "":
                    veces = 0
                    while i + (veces + 2) * k <= n:
                        siguiente_chunk = palabras[i + (veces + 1) * k : i + (veces + 2) * k]
                        if [re.sub(r'[^\w]', '', w.lower()) for w in siguiente_chunk] == c1_norm: veces += 1
                        else: break
                    resultado.extend(chunk1)
                    i += (2 + veces) * k
                    bucle_detectado = True
                    break
        if not bucle_detectado:
            resultado.append(palabras[i])
            i += 1
    return " ".join(resultado)

print("🚀 Motor Whisper conectado a la API de GitHub/Railway. Escuchando archivos...")

while True:
    try:
        # 1. Preguntarle a Railway si el usuario subió un video
        resp = requests.get(f"{API_URL}/api/worker/next")
        data = resp.json()
        
        if data.get("hay_tarea"):
            task_id = data["task_id"]
            nombre = data["nombre"]
            print(f"📥 ¡Video/Audio detectado! Descargando: {nombre}")
            
            # 2. Descargar el archivo temporalmente adonde está corriendo la IA
            local_path = f"./{nombre}"
            audio_resp = requests.get(f"{API_URL}/api/worker/download/{task_id}")
            with open(local_path, "wb") as f:
                f.write(audio_resp.content)
            
            print(f"🎙️ Transcribiendo con Whisper...")
            resultado = model.transcribe(local_path, fp16=torch.cuda.is_available())
            texto_sucio = resultado["text"].strip()
            
            # Aplicar tu lógica anti-bucles limpia de LibriSpeech
            texto_final = quitar_bucles_redundantes(texto_sucio)
            
            print("📤 Enviando libreto procesado de vuelta a la web...")
            requests.post(f"{API_URL}/api/worker/webhook", json={
                "task_id": task_id,
                "texto": texto_final
            })
            
            # Limpieza profunda de memoria
            if os.path.exists(local_path): os.remove(local_path)
            gc.collect()
            if torch.cuda.is_available(): torch.cuda.empty_cache()
            print("✅ Transcripción enviada con éxito.")
            
    except Exception as e:
        # Bucle de espera silencioso si no hay videos en cola
        pass
    time.sleep(3)
