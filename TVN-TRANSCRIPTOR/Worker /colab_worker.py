import whisperx
import torch
import re
import gc
import time
import requests
import os

# CONFIGURACIÓN
API_URL = "https://tu-proyecto.up.railway.app"  # <-- REEMPLAZA CON TU URL DE RAILWAY
MI_HF_TOKEN = ""  # Agrega tu token de Hugging Face si usas diarización de voces

device = "cuda" if torch.cuda.is_available() else "cpu"
compute_type = "float16" if torch.cuda.is_available() else "int8"

print(f"🤖 Buscando modelos de IA en modo: {device}...")
model = whisperx.load_model("turbo", device, compute_type=compute_type, language="es")

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

def procesar_transcripcion(file_path):
    resultado = model.transcribe(file_path, batch_size=16)
    try:
        diarize_model = whisperx.DiarizationPipeline(use_auth_token=MI_HF_TOKEN if MI_HF_TOKEN else None, device=device)
        diarize_segments = diarize_model(file_path)
        resultado_final = whisperx.assign_word_speakers(diarize_segments, resultado)
    except Exception as e:
        print(f"Modo básico (sin voces) debido a: {e}")
        resultado_final = resultado

    texto_libreto, ultimo_hablante = "", None
    if "segments" in resultado_final:
        for segment in resultado_final["segments"]:
            hablante = segment.get("speaker", "VOZ").replace("SPEAKER_", "HABLANTE ")
            texto_limpio = quitar_bucles_redundantes(segment['text'].strip())
            if not texto_limpio or len(texto_limpio) < 2: continue
            if hablante != ultimo_hablante:
                texto_libreto += f"\n--- {hablante} ---\n"
                ultimo_hablante = hablante
            texto_libreto += f"{texto_limpio} "
    return texto_libreto.strip()

print("🚀 Worker Conectado. Escuchando peticiones de la API...")
while True:
    try:
        resp = requests.get(f"{API_URL}/api/worker/next")
        data = resp.json()
        
        if data.get("hay_tarea"):
            task_id = data["task_id"]
            nombre = data["nombre"]
            print(f"📥 Descargando archivo: {nombre}")
            
            local_path = f"/content/{nombre}"
            audio_resp = requests.get(f"{API_URL}/api/worker/download/{task_id}")
            with open(local_path, "wb") as f:
                f.write(audio_resp.content)
            
            print(f"🎙️ Transcribiendo con WhisperX...")
            texto_final = procesar_transcripcion(local_path)
            
            print("📤 Enviando resultado a la API...")
            requests.post(f"{API_URL}/api/worker/webhook", json={
                "task_id": task_id,
                "texto": texto_final
            })
            
            if os.path.exists(local_path): os.remove(local_path)
            gc.collect()
            if torch.cuda.is_available(): torch.cuda.empty_cache()
            print("✅ Tarea completada con éxito.")
    except Exception as e:
        print(f"Esperando nueva petición... (Error: {e})")
    time.sleep(5)
