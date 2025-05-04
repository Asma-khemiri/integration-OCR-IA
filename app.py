from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import requests
import tempfile
import os
from ocr.abbyy_service import send_image_to_abbyy, get_task_status
from ai.gemini_service import extract_invoice_data

app = Flask(__name__)
CORS(app)  # Pour accepter les appels venant de ReactJS

@app.route('/extract', methods=['POST'])
def extract_invoice_data_api():
    data = request.get_json()
    image_url = data.get('imageUrl')

    if not image_url:
        return jsonify({"error": "Image URL is required"}), 400

    temp_file = None

    try:
        print("Téléchargement de l'image...")
        # Télécharger l'image temporairement
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        response = requests.get(image_url)

        if response.status_code != 200:
            print("Erreur téléchargement image")
            return jsonify({"error": "Impossible de télécharger l'image"}), 400

        temp_file.write(response.content)
        temp_file.close()

        print(f"Image téléchargée : {temp_file.name}")

        # Envoyer à ABBYY OCR
        task_id = send_image_to_abbyy(temp_file.name)
        if not task_id:
            print("Erreur envoi OCR")
            return jsonify({"error": "Échec de l'envoi OCR"}), 500

        print(f"Tâche OCR envoyée, task_id={task_id}")
        print("Attente du traitement OCR...")

        # Attendre que l'OCR soit terminé
        ocr_text = None
        for attempt in range(10):
            print(f"Vérification OCR tentative {attempt + 1}/10...")
            time.sleep(3)
            ocr_text = get_task_status(task_id)
            if ocr_text:
                try:
                    ocr_text = ocr_text.encode('latin1').decode('utf-8')
                except Exception as e:
                    print(f"Erreur correction encodage : {e}")
                print("OCR terminé")
                break

        if not ocr_text:
            print("Timeout OCR après 10 tentatives")
            return jsonify({"error": "OCR timeout"}), 500

        print("Extraction Gemini...")
        # Envoyer à Gemini
        extracted_data = extract_invoice_data(ocr_text)

        if extracted_data:
            print("Extraction réussie")
            return jsonify(extracted_data), 200
        else:
            print("Échec d'extraction Gemini")
            return jsonify({"error": "Extraction échouée"}), 500

    except Exception as e:
        print(f"Erreur serveur : {str(e)}")
        return jsonify({"error": str(e)}), 500

    finally:
        # Toujours nettoyer le fichier temporaire même si erreur
        if temp_file:
            try:
                os.unlink(temp_file.name)
                print("Fichier temporaire supprimé")
            except Exception as cleanup_error:
                print(f"Erreur suppression fichier temporaire: {str(cleanup_error)}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
