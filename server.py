import json
import base64
import requests
from flask import Flask, request, jsonify
import os
import threading
from threading import Lock

app = Flask(__name__)

# Ruta base para los archivos
BASE_PATH = "./"

# Archivos que contienen los números que ya han recibido los mensajes
sent_numbers_file = os.path.join(BASE_PATH, "sent_numbers.txt")
precio_file = os.path.join(BASE_PATH, "precio.txt")  # Cambiado de tienda.txt a precio.txt

# Bloqueos para acceso a archivos
sent_numbers_lock = Lock()
precio_file_lock = Lock()  # Cambiado de tienda_file_lock a precio_file_lock

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
    os.path.join(BASE_PATH, "video2.mp4"),
    os.path.join(BASE_PATH, "video3.mp4"),
    os.path.join(BASE_PATH, "video4.mp4"),
    os.path.join(BASE_PATH, "video5.mp4")
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

# Diccionarios para manejar las sesiones y bloqueos por usuario
active_sessions = {}
session_locks = {}

def encode_file_to_base64(file_path):
    with open(file_path, "rb") as file:
        return base64.b64encode(file.read()).decode('utf-8')

def has_received_catalog(phone_number):
    if not os.path.exists(sent_numbers_file):
        return False
    with sent_numbers_lock:
        with open(sent_numbers_file, 'r') as file:
            return phone_number in file.read()

def mark_as_sent(phone_number):
    with sent_numbers_lock:
        with open(sent_numbers_file, 'a') as file:
            file.write(phone_number + '\n')

def has_received_precio(phone_number):
    if not os.path.exists(precio_file):
        return False
    with precio_file_lock:
        with open(precio_file, 'r') as file:
            return phone_number in file.read()

def mark_as_precio_sent(phone_number):
    with precio_file_lock:
        with open(precio_file, 'a') as file:
            file.write(phone_number + '\n')

def send_message(phone_number, message_text):
    """Función para enviar un mensaje de texto."""
    print(f"Enviando mensaje: {message_text} a {phone_number}")
    
    payload = {
        "Phone": phone_number,
        "Body": message_text
    }

    response = requests.post(wuzapi_url_text, json=payload, headers={"token": wuzapi_token})
    print(f"Respuesta de Wuzapi: {response.json()}")

def send_pdf(phone_number, pdf_filename, pdf_name):
    """Función para enviar un PDF."""
    print(f"Enviando PDF {pdf_name} a {phone_number}")
    
    encoded_pdf = encode_file_to_base64(pdf_filename)
    
    payload = {
        "Phone": phone_number,
        "Document": f"data:application/octet-stream;base64,{encoded_pdf}",
        "FileName": pdf_name
    }

    response = requests.post(wuzapi_url_document, json=payload, headers={"token": wuzapi_token})
    print(f"Respuesta de Wuzapi: {response.json()}")

def send_video(phone_number, video_filename):
    """Función para enviar un video sin texto."""
    if not os.path.exists(video_filename):
        print(f"Error: {video_filename} no existe.")
        return
    
    print(f"Enviando video {video_filename} a {phone_number}")
    
    encoded_video = encode_file_to_base64(video_filename)
    
    payload = {
        "Phone": phone_number,
        "Video": f"data:video/mp4;base64,{encoded_video}",
        "FileName": os.path.basename(video_filename)
    }

    response = requests.post(wuzapi_url_video, json=payload, headers={"token": wuzapi_token})
    print(f"Respuesta de Wuzapi: {response.json()}")

@app.route('/webhook', methods=['POST'])
def webhook():
    # Obtener los datos entrantes
    if request.content_type == 'application/json':
        data = request.get_json()
    elif request.content_type == 'application/x-www-form-urlencoded':
        data = request.form.to_dict()
        if 'jsonData' in data:
            data['jsonData'] = json.loads(data['jsonData'])
    else:
        return jsonify({"error": "Unsupported Media Type"}), 415

    print(f"Datos recibidos: {data}")  # Para depuración

    try:
        sender_full = data['jsonData']['event']['Info']['Sender']
        sender = sender_full.split('@')[0]  # Extraer solo el número de teléfono
    except KeyError:
        return jsonify({"error": "Bad Request: No sender found"}), 400

    # Obtener el texto del mensaje si está disponible
    message_text = ''
    try:
        message_text = data['jsonData']['event']['Message']['conversation']
    except KeyError:
        pass  # El mensaje puede no contener 'conversation' en algunos casos

     # Procesar el texto del mensaje para verificar palabras clave
    keywords = ["cuantos", "kuantos", "cuanto", "kuanto", "knto",
    "mínimo", "minimo", "mínim", "minim", "mín.",
    "pedido", "ped", "pido", "pedidos", "pidos",
    "cotización", "cotizacion", "cotisación", "cotisacion", "kotización", "kotizacion", "kotisación", "kotisacion",
    "interés", "interes", "interéz", "interez", "interesa", "intereza", 
    "necesito", "nesesito", "necesitó", "nesesitó", "necesita", "nesesita", "necesitá", "nesesitá",
    "quisiera", "kisiera", "quisierá", "kisierá", "kiziera", "quisierá",
    "ventá", "venta", "vta", "vtas", "ventas", 
    "mayoréo", "mayoreo", "mayorista", "mayorístas", "mayoristas", "mayoría", "mayoria", 
    "reloj", "relojes", "relojéz", "relojesz",
    "gshock", "gshok", "gshóc", "gshoc", 
    "rolex", "rolez", "roléx", "rolx", "r0lex",
    "sé", "se",
    "té", "te",
    "cuánto", "cuanto", "kuánto", "kuanto", "kánto", "kanto", "kuántos", "kuantos", "kántos", "kantos", 
    "precio", "preció", "presió", "prezió", "prció", "preco", "prezó", "prció",
    "perció", "prazió", "preçió", "preçios", "preçi0", "pr3ció", "preçi0s",
    "undidad", "unidád", "unidá.", "unidádes",
    "pieza", "piezá", "pz", "piezas", "pzás", "pzs",
    "dozéna", "docena", "docénas", "dozenas",
    "ócho", "ocho", "ochó", "och0",
    "cinco", "cínco", "5nco", "5",
    "séis", "seis", "seís", "6",
    "síete", "siete", "síete", "7te",
    "nueve", "núeve", "nuevé", "9ve",
    "diez", "diéz", "diézz", "di10z",
    "veinte", "veínte", "veintez", "20inte",
    "séis", "seís", "ceys", "6eís",
    "costo", "kosto", "coste", "koste","a","si","en","y","por","el","de","a", "ante", "bajo", "cabe", "con", "contra", "de", "desde", "durante", 
    "en", "entre", "hacia", "hasta", "mediante", "para", "por", "según", 
    "sin", "so", "sobre", "tras","precio", "presio", "prezio", "prezio", "precios", "presios", "prezios",
    "prcio", "przio", "przo", "prco", "prec", "prc", "pre", "prcio", "prezo", "preco",
    "percio", "prazio", "preçio", "preçios", "preçi0", "pr3cio", "preçi0s",
    "unidad", "unid", "unids", "unid.", "und", "unds", "unds.","unida","u","un","uni","unid","unida",
    "unidades", "unidaddes", "uniadades", "unidadd", "unidads", "unidats",
    "ud", "uds", "ud.", "uds.", "u.", "u", "uni", "un", "uns",
    "undidad", "unidá", "unidá.", "unidádes",
    "pieza", "pza", "pz", "piezas", "pzas", "pzs",
    "docena", "dozena", "docna", "docnea", "docen", "dozen",
    "docenas", "dozenas", "docenaz", "dozenaz",
    "doce", "doze", "d0ce", "d0ze", "doçe",
    "doc", "doz", "dz", "dza", "dzn",
    "12", "1docena", "1dozena", "uno2", "unodos",
    "media", "meia", "1/2", "6", "seis",
    "oferta", "ofrta", "ofrt", "ofertas", "ofrtas", "ofrts",
    "descuento", "deskuento", "desc", "dcto", "dctos",
    "promo", "promos", "promocion", "promozion", "promociones", "promoziones",
    "cantidad", "cant", "cantd", "cantid", "kantidad", "kantidad",
    "volumen", "vol", "volum", "volúmen", "volúmenes",
    "lote", "lot", "lots", "lotes",
    "mínimo", "minimo", "minim", "mínim", "min", "min.",
    "pedido", "ped", "pido", "pedidos", "pidos",
    "cotizacion", "cotiz", "cotisacion", "kotizacion", "kotisacion",
    "interesa", "intereza", "interes", "interez",
    "necesito", "nesesito", "nesecito", "nececito",
    "quisiera", "kisiera", "kiziera", "kisier",
    "venta", "vta", "vtas", "ventas",
    "mayoreo", "mayorista", "mayoristas", "mayoréo",
    "mayor", "mayores", "mayoria",
    "reloj", "relojes", "relojz", "rloj", "rlojes", "relojes",
    "gshock", "gshok", "gshoc", "gsh0ck", "gsh0c", "gshockz",
    "rolex", "rolez", "rolx", "r0lex", "rolexz", "rolexes",
    "uno", "u1", "un", "1n", "uno", "uno.", "unn", "uno1", "un0", "uun",
    "dos", "d0s", "2", "doz", "doss", "dosz", "dós", "d0z", "d0ss", "dosss", 
    "tres", "3s", "3", "tr3s", "tresz", "tress", "trezz", "tre3z", 
    "cuatro", "4tro", "4", "kuatro", "cu4tro", "quat", "cua4tro", "k4tro", 
    "cinco", "5nco", "5", "sinko", "cincoo", "cinko", "s1nco", 
    "seis", "6is", "6", "seiss", "seyz", "ceys", "6eis", 
    "siete", "7te", "7", "s1ete", "site", "si7e", 
    "ocho", "8cho", "8", "ochoo", "och0", "och", 
    "nueve", "9ve", "9", "nve", "nu3ve", "nuevve", "nuevev", 
    "diez", "10z", "10", "diz", "diezz", "di10z", 
    "once", "11ce", "11", "onz", "oncez", "oncez.", 
    "doce", "12ce", "12", "doc", "doz", "d0z", 
    "trece", "13ce", "13", "t13ce", "trecz", "treczz", 
    "catorce", "14rce", "14", "kat0rce", "quatorce", "kat1rce", 
    "quince", "15nce", "15", "qince", "k1nce", "quinz", 
    "dieciseis", "16ciseis", "16", "d16", "di3ci6eis", 
    "diecisiete", "17ciseite", "17", "17c", "di3ci7", 
    "dieciocho", "18c1cho", "18", "diec1och0", "18cho", 
    "diecinueve", "19cinve", "19", "diec1nueve", "19nv", 
    "veinte", "20inte", "20", "ve1nte", "viente", "v20", "ve1nt", 
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20"]
    
    
    message_lower = message_text.lower()

    # Asegurar que solo un hilo procese la interacción de un cliente
    if sender not in session_locks:
        session_locks[sender] = Lock()

    with session_locks[sender]:
        if not has_received_catalog(sender):
            # Es la primera vez que nos contacta, enviar mensajes de bienvenida
            if sender not in active_sessions:
                active_sessions[sender] = True
                threading.Thread(target=send_welcome_pdfs_videos_to_client, args=(sender,)).start()
        else:
            # Ya ha recibido los mensajes de bienvenida
            #if any(keyword in message_lower for keyword in keywords):
                # El mensaje contiene una de las palabras clave
                if not has_received_precio(sender):
                    threading.Thread(target=send_precio_message, args=(sender,)).start()

    return jsonify({"status": "success"}), 200

def send_precio_message(sender):
    # Enviar los dos mensajes solicitados
    messages = [
        "⌚Por DOCENA relojes 50 soles",
        "¿Cuántas unidades desea llevar? 🙌☺️"
    ]
    for message in messages:
        send_message(sender, message)
    mark_as_precio_sent(sender)
    # Limpiar la sesión y el bloqueo
    session_locks.pop(sender, None)

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
    
    # Enviar videos
    for video in video_files:
        send_video(sender, video)

    mark_as_sent(sender)
    active_sessions.pop(sender, None)
    session_locks.pop(sender, None)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8765, debug=True)
