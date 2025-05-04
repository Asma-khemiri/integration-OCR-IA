from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import requests
import tempfile
import os
from ocr.abbyy_service import send_image_to_abbyy, get_task_status
from ai.gemini_service import extract_invoice_data

app = Flask(__name__)
CORS(app)  # To allow calls from ReactJS

@app.route('/extract', methods=['POST'])
def extract_invoice_data_api():
    data = request.get_json()
    image_url = data.get('imageUrl')

    if not image_url:
        return jsonify({"error": "Image URL is required"}), 400

    temp_file = None

    try:
        print("Downloading image...")
        # Download the image temporarily
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        response = requests.get(image_url)

        if response.status_code != 200:
            print("Image download error")
            return jsonify({"error": "Failed to download the image"}), 400

        temp_file.write(response.content)
        temp_file.close()

        print(f"Image downloaded: {temp_file.name}")

        # Send to ABBYY OCR
        task_id = send_image_to_abbyy(temp_file.name)
        if not task_id:
            print("OCR submission error")
            return jsonify({"error": "Failed to submit to OCR"}), 500

        print(f"OCR task submitted, task_id={task_id}")
        print("Waiting for OCR processing...")

        # Wait for OCR to finish
        ocr_text = None
        for attempt in range(10):
            print(f"OCR check attempt {attempt + 1}/10...")
            time.sleep(3)
            ocr_text = get_task_status(task_id)
            if ocr_text:
                try:
                    ocr_text = ocr_text.encode('latin1').decode('utf-8')
                except Exception as e:
                    print(f"Encoding correction error: {e}")
                print("OCR completed")
                break

        if not ocr_text:
            print("OCR timeout after 10 attempts")
            return jsonify({"error": "OCR timeout"}), 500

        print("Gemini extraction...")
        # Send to Gemini
        extracted_data = extract_invoice_data(ocr_text)

        if extracted_data:
            print("Extraction successful")
            return jsonify(extracted_data), 200
        else:
            print("Gemini extraction failed")
            return jsonify({"error": "Extraction failed"}), 500

    except Exception as e:
        print(f"Server error: {str(e)}")
        return jsonify({"error": str(e)}), 500

    finally:
        # Always clean up the temporary file even if there's an error
        if temp_file:
            try:
                os.unlink(temp_file.name)
                print("Temporary file deleted")
            except Exception as cleanup_error:
                print(f"Error deleting temporary file: {str(cleanup_error)}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
