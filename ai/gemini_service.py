import google.generativeai as genai
import json
import re

genai.configure(api_key="AIzaSyAFbWVpbTwkIYvOh9QDkMRu36M3eIiEYig")

def generate_gemini_prompt(text):
    return f"""
You are a smart assistant that extracts structured data from the OCR content of invoices.

Your goal is to extract the following fields:

- "TVA" 
- "total_amount" (the total amount to pay)
- "client_name" (the name of the person or company the invoice is addressed to)
- "invoice_date" (the date of the invoice, ideally in dd/mm/yyyy format)

Guidelines:
- The invoice text may be written in various languages (French, English, Spanish, Arabic, etc.). Detect the language automatically.
- Invoice formats may vary (columns, paragraphs, informal layouts).
- If a piece of information is not clearly found, return `"null"` for that field.
- Do **not** make assumptions or hallucinate values.
- Ignore any data not explicitly listed above.
- Your response must be in pure JSON format.

OCR Text:



\"\"\"
{text}
\"\"\"

"""

def analyze_invoice_with_gemini(text):
    model = genai.GenerativeModel(model_name="models/gemini-1.5-pro")
    prompt = generate_gemini_prompt(text)
    response = model.generate_content(prompt)

    # Fermeture propre de la connexion gRPC
    try:
        model._client.transport.grpc_channel.close()
    except Exception:
        pass

    return response.text


def process_gemini_json_response(response_text):
    response_text = re.sub(r"```json\s*|\s*```", "", response_text).strip()
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        print("\nErreur JSON :\n", response_text)
        return None
def process_invoice_text(text):
    raw_response = analyze_invoice_with_gemini(text)
    return process_gemini_json_response(raw_response)

def extract_invoice_data(text):
    return process_invoice_text(text)
