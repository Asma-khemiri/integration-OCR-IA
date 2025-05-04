import google.generativeai as genai
import json
import re

# Configure Gemini
genai.configure(api_key="AIzaSyAFbWVpbTwkIYvOh9QDkMRu36M3eIiEYig")

def generate_gemini_prompt(text):
    return f"""
You are a smart assistant that extracts structured data from the OCR content of invoices.

Your goal is to extract the following fields:

- "siret_number" (the French SIRET number)
- "invoice_number" (the invoice number)
- "TVA Number" (the VAT number)
- "invoice_date" (the date of the invoice, ideally in dd/mm/yyyy format)
- "TVA" (the VAT amount)
- "HT" (the amount excluding tax)
- "TTC" (the total amount including tax)
- "client_name" (the client's name)
- "currency" (the currency of the amounts)

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
    model = genai.GenerativeModel(model_name="models/gemini-1.5-pro")
    prompt = generate_gemini_prompt(text)
    response = model.generate_content(prompt)
    return response.text

def clean_extracted_data(data):

    def split_amount_and_currency(value):
        if not value or value == "null":
            return None, None

        value = re.sub(r'(?<=\d)\s+(?=\d)', '', value)

        match = re.search(r"(\d+(?:[.,]\d{1,3})?)\s*([^\d\s]+)?", value)
        if match:
            amount = match.group(1).replace(",", ".")
            currency = match.group(2) if match.group(2) else None
            return amount, currency
        return value, None

    if "TVA" in data:
        amount, _ = split_amount_and_currency(data["TVA"])
        if amount:
            amount = amount.replace("%", "").strip()
        data["TVA"] = amount

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
        print("\nRaw JSON received from Gemini:\n", parsed)
        cleaned = clean_extracted_data(parsed)
        return cleaned
    except json.JSONDecodeError:
        print("\nJSON parsing error:\n", response_text)
        return None

def process_invoice_text(text):
    raw_response = analyze_invoice_with_gemini(text)
    return process_gemini_json_response(raw_response)

def extract_invoice_data(text):
    return process_invoice_text(text)
