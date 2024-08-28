import json
import base64
import requests
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Ruta al archivo de seguimiento de números
sent_numbers_file = 'sent_numbers.txt'

# Nombres de los archivos PDF
pdf_files = [
    "CARTERAS_Dama.pdf",
    "RELOJES_CABALLERO.pdf",
    "MORRALES_Caballero.pdf",
    "MORRALES_Dama.pdf",
    "RELOJES_Dama.pdf"
]

# Wuzapi API endpoint y token
wuzapi_url = "http://localhost:8080/chat/send/document"
wuzapi_token = "jhon"

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

    if not has_received_catalog(sender):
        for pdf in pdf_files:
            send_pdf(sender, pdf)
        mark_as_sent(sender)
    
    return jsonify({"status": "success"}), 200

def send_pdf(phone_number, pdf_filename):
    print(f"Sending PDF {pdf_filename} to {phone_number}")
    
    encoded_pdf = encode_file_to_base64(pdf_filename)
    
    payload = {
        "Phone": phone_number,
        "Document": f"data:application/octet-stream;base64,{encoded_pdf}",
        "FileName": pdf_filename
    }

    response = requests.post(wuzapi_url, json=payload, headers={"token": wuzapi_token})
    print(f"Response from Wuzapi: {response.json()}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8765, debug=True)
