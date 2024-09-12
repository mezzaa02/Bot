import json
import base64
import requests
from flask import Flask, request, jsonify
import os
import threading
from threading import Lock

app = Flask(__name__)

# Ruta base para los archivos (ajusta esta ruta si los archivos están en otra carpeta)
BASE_PATH = "./"  # Si los archivos están en la misma carpeta que el script
# Si los videos están en una subcarpeta llamada 'videos', usa esta ruta:
# BASE_PATH = "./videos/"

# Archivo que contiene los números que ya han recibido los PDFs y videos
sent_numbers_file = os.path.join(BASE_PATH, "sent_numbers.txt")

# Nombres de los archivos PDF
pdf_names = ["RELOJES de Caballero.pdf", "CARTERAS de Dama.pdf", "RELOJES de Dama.pdf", "MORRALES de Dama.pdf", "MORRALES de Caballero.pdf"]
pdf_files = [os.path.join(BASE_PATH, pdf) for pdf in pdf_names]

# Mensajes de bienvenida
welcome_messages = [
    "👋💚 *Buenas* 🤗",
    "Somos empresa 💼 *RUC: 20610868577* Registrada desde *1993* 🥳⭐⭐⭐⭐⭐",
    "✅🩷🩵 Precios *POR DOCENA*\n(si lleva 12 productos *en TOTAL* ) 🛒✨\n▫️⌚Relojes: *50 soles*\n▫️👜Carteras: *50 soles*\n▫️💼Morrales: *50 soles*\n▫️ Billeteras: *20 soles*\n▫️👛Monederos: *15 soles*\n▫️👝Chequeras: *30 soles*\n▫️Correas: *30 soles*"
]

# Nombres de los archivos de video
video_files = [
    #os.path.join(BASE_PATH, "video1.mp4"),  # Este video lleva un mensaje (separado)
    os.path.join(BASE_PATH, "video2.mp4"),
    os.path.join(BASE_PATH, "video3.mp4"),
    os.path.join(BASE_PATH, "video4.mp4"),
    os.path.join(BASE_PATH, "video5.mp4"),
    os.path.join(BASE_PATH, "video6.mp4")
]

# Texto para el primer video
first_video_message = """🥳Replica *A1 Rolex* ✨😍
⌚Por *DOCENA* relojes *50 soles*
💚 *CUALQUIER MODELO mismos precios* 🛍️"""

# Wuzapi API endpoint y token
wuzapi_url_text = "http://localhost:8080/chat/send/text"
wuzapi_url_document = "http://localhost:8080/chat/send/document"
wuzapi_url_video = "http://localhost:8080/chat/send/video"
wuzapi_token = "jhon"

# Diccionario para manejar las sesiones y su respectivo bloqueo
active_sessions = {}
session_locks = {}

def encode_file_to_base64(file_path):
    with open(file_path, "rb") as file:
        return base64.b64encode(file.read()).decode('utf-8')

def has_received_catalog(phone_number):
    if not os.path.exists(sent_numbers_file):
        return False
    with open(sent_numbers_file, 'r') as file:
        return phone_number in file.read()

def mark_as_sent(phone_number):
    with open(sent_numbers_file, 'a') as file:
        file.write(phone_number + '\n')

def send_message(phone_number, message_text):
    """Función para enviar un mensaje de texto."""
    print(f"Sending message: {message_text} to {phone_number}")
    
    payload = {
        "Phone": phone_number,
        "Body": message_text
    }

    response = requests.post(wuzapi_url_text, json=payload, headers={"token": wuzapi_token})
    print(f"Response from Wuzapi: {response.json()}")

def send_pdf(phone_number, pdf_filename, pdf_name):
    """Función para enviar un PDF."""
    print(f"Sending PDF {pdf_name} to {phone_number}")
    
    encoded_pdf = encode_file_to_base64(pdf_filename)
    
    payload = {
        "Phone": phone_number,
        "Document": f"data:application/octet-stream;base64,{encoded_pdf}",
        "FileName": pdf_name  # Aquí enviamos solo el nombre del archivo
    }

    response = requests.post(wuzapi_url_document, json=payload, headers={"token": wuzapi_token})
    print(f"Response from Wuzapi: {response.json()}")

def send_video(phone_number, video_filename):
    """Función para enviar un video sin texto."""
    # Verificar si el archivo de video existe
    if not os.path.exists(video_filename):
        print(f"Error: {video_filename} no existe.")
        return
    
    print(f"Sending video {video_filename} to {phone_number}")
    
    encoded_video = encode_file_to_base64(video_filename)
    
    payload = {
        "Phone": phone_number,
        "Video": f"data:video/mp4;base64,{encoded_video}",
        "FileName": os.path.basename(video_filename)  # Aquí enviamos solo el nombre del archivo
    }

    response = requests.post(wuzapi_url_video, json=payload, headers={"token": wuzapi_token})
    print(f"Response from Wuzapi: {response.json()}")

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.content_type == 'application/json':
        data = request.get_json()
    elif request.content_type == 'application/x-www-form-urlencoded':
        data = request.form.to_dict()
        if 'jsonData' in data:
            data['jsonData'] = json.loads(data['jsonData'])
    else:
        return jsonify({"error": "Unsupported Media Type"}), 415

    try:
        sender = data['jsonData']['event']['Info']['Sender']
    except KeyError:
        return jsonify({"error": "Bad Request: No sender found"}), 400

    # Asegurarse de que solo un hilo procese la primera interacción de un cliente
    if sender not in session_locks:
        session_locks[sender] = Lock()

    with session_locks[sender]:  # Bloquear la sesión para este cliente específico
        if sender not in active_sessions:
            active_sessions[sender] = True  # Marcar la sesión como activa
            if not has_received_catalog(sender):
                # Utilizar threading para evitar bloquear el webhook
                threading.Thread(target=send_welcome_pdfs_videos_to_client, args=(sender,)).start()

    return jsonify({"status": "success"}), 200

def send_welcome_pdfs_videos_to_client(sender):
    """Envía los mensajes de bienvenida, PDFs y videos al cliente."""
    # Enviar mensajes de bienvenida
    for message in welcome_messages:
        send_message(sender, message)
    
    # Enviar PDFs
    for pdf_filename, pdf_name in zip(pdf_files, pdf_names):
        send_pdf(sender, pdf_filename, pdf_name)

    # Enviar el mensaje para el primer video antes de enviar el video
    send_message(sender, first_video_message)
    
    # Enviar videos (sin mensajes)
    for video in video_files:
        send_video(sender, video)

    mark_as_sent(sender)
    active_sessions.pop(sender, None)  # Eliminar la sesión después de enviar los PDFs y videos
    session_locks.pop(sender, None)  # Eliminar el bloqueo de sesión después de completar el envío

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8765, debug=True)
