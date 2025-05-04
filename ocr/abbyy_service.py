from abbyy_config import ABBYY_APP_ID, ABBYY_PASSWORD, OCR_API_URL, TASK_STATUS_URL
import base64
import requests

def get_auth_header():
    credentials = f"{ABBYY_APP_ID}:{ABBYY_PASSWORD}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    return {'Authorization': f'Basic {encoded_credentials}'}

def send_image_to_abbyy(image_path):
    with open(image_path, 'rb') as file:
        files = {'file': file}
        params = {'exportFormat': 'txt'}
        response = requests.post(OCR_API_URL, headers=get_auth_header(), params=params, files=files)

    if response.status_code == 200:
        print("Image envoyée avec succès.")
        return response.json().get('taskId')
    else:
        print(f"Erreur envoi image [{response.status_code}]: {response.text}")
        return None

def get_task_status(task_id):
    url = f"{TASK_STATUS_URL}?taskId={task_id}"
    response = requests.get(url, headers=get_auth_header())

    if response.status_code == 200:
        data = response.json()
        status = data.get('status', '')

        if status == 'Completed':
            result_url = data['resultUrls'][0]
            result = requests.get(result_url)
            return result.text if result.status_code == 200 else None
        elif status == 'InProgress':
            print("OCR en cours...")
        elif status == 'Queued':
            print("En file d'attente...")
        else:
            print(f"Erreur statut : {status}")
    else:
        print(f"Erreur status API : {response.status_code}")
    return None
