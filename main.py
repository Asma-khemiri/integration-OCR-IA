from ocr.abbyy_service import send_image_to_abbyy, get_task_status
import time
from ai.gemini_service import extract_invoice_data
def main():

    image_path = "C:/Users/lenovo/Desktop/OCR_IA/fact1.jpeg"
    task_id = send_image_to_abbyy(image_path)
    if not task_id:
        print("Impossible de lancer l'OCR")
        return

    print("Attente du traitement OCR...")
    ocr_text = None
    for _ in range(10):
        time.sleep(3)
        ocr_text = get_task_status(task_id)
        if ocr_text:
            break

    if not ocr_text:
        print("Échec de l'OCR après plusieurs tentatives")
        return

    print("\nTexte OCR extrait :\n", ocr_text)

    print("\n Envoi à Gemini pour extraction des données...")
    extracted_data = extract_invoice_data(ocr_text)

    if extracted_data:
        print("\nDonnées extraites par Gemini :")
        print(extracted_data)
    else:
        print("Impossible d’extraire les données avec Gemini.")

if __name__ == "__main__":
    main()
