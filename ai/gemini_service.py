import google.generativeai as genai
import json
import re

# Configurer Gemini
genai.configure(api_key="AIzaSyDYTDzcd7_oBVwEpve5D5BuLmsQgumhGI4")


def generate_gemini_prompt(text):
    return f"""
You are a smart assistant that extracts structured data from the OCR content of invoices.

Your goal is to extract the following fields from the invoice:

   Invoice Metadata:
    - "invoice_number" (the invoice number)
    - "invoice_date" (the date of the invoice, ideally in dd/mm/yyyy format)
    - "due_date" (format: dd/mm/yyyy)
    - "currency" 


    Seller Informations:
    - "seller_name"
    - "seller_address"
    - "seller_phone"
    - "seller_siret_number" (French business ID number)

    Customer Informations:
    - "customer_name"
    - "customer_address"
    - "customer_phone"


    Amounts:
    - "tva" (the VAT amount)
    - "tva_number" (the TVA number)
    - "tva_Rate"

    - "ht" (the amount excluding tax)
    - "ttc" (the total amount with tax)
    - "discount"

Guidelines:
- The invoice text may be written in various languages (French, English, Spanish, Arabic, etc.). Detect the language automatically.
- Invoice formats may vary (columns, paragraphs, informal layouts).
- If a piece of information is not clearly found, return `"null"` for that field.
- Do **not** hallucinate or invent data.
- For "total_amount", extract only the number, and for "currency", extract the currency symbol.
- Your response must be in pure JSON format.

OCR Text:




\"\"\"{text}\"\"\"
"""


def analyze_invoice_with_gemini(text):
    model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")
    prompt = generate_gemini_prompt(text)
    response = model.generate_content(prompt)

    return response.text


def clean_extracted_data(data):
    def split_amount_and_currency(value):
        if not value or value == "null":
            return None, None

        value = str(value)

        value = re.sub(r'(?<=\d)\s+(?=\d)', '', value)

        match = re.search(r"(\d+(?:[.,]\d{1,3})?)\s*([^\d\s]+)?", value)
        if match:
            amount = match.group(1).replace(",", ".")  # remplacer virgule par point
            currency = match.group(2) if match.group(2) else None
            return amount, currency
        return value, None

    if "tva" in data:
        amount, _ = split_amount_and_currency(data["tva"])
        if amount:
            amount = amount.replace("%", "").strip()
        data["tva"] = amount

    if "tva_Rate" in data:
        if data["tva_Rate"] and isinstance(data["tva_Rate"], str):
            data["tva_Rate"] = data["tva_Rate"].replace("%", "").strip()

    if "total_amount" in data:
        amount, currency = split_amount_and_currency(data["total_amount"])
        data["total_amount"] = amount
        if "currency" not in data or not data["currency"] or data["currency"] == "null":
            data["currency"] = currency

    return data


def process_gemini_json_response(response_text):
    response_text = re.sub(r"```json\s*|\s*```", "", response_text).strip()
    try:
        parsed = json.loads(response_text)
        print("\n JSON brut reçu de Gemini:\n", parsed)
        cleaned = clean_extracted_data(parsed)

        # Convert snake_case to camelCase
        camel_cased = convert_keys_to_camel_case(cleaned)
        return camel_cased

    except json.JSONDecodeError:
        print("\nErreur JSON :\n", response_text)
        return None


def process_invoice_text(text):
    raw_response = analyze_invoice_with_gemini(text)
    return process_gemini_json_response(raw_response)


def to_camel_case(snake_str):
    parts = snake_str.split('_')
    return parts[0] + ''.join(word.capitalize() for word in parts[1:])


def convert_keys_to_camel_case(data):
    if isinstance(data, dict):
        return {to_camel_case(k): convert_keys_to_camel_case(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_keys_to_camel_case(i) for i in data]
    else:
        return data


def extract_invoice_data(text):
    result = process_invoice_text(text)
    print("\n Final extracted data (camelCase):\n", result)
    return result