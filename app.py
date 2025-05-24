from flask import Flask, request, jsonify
import requests
import tempfile
import os
import fitz  # PyMuPDF
import pdfplumber
import pytesseract
from pdf2image import convert_from_path

app = Flask(__name__)

def extract_text(file_url):
    try:
        # Download the file
        response = requests.get(file_url)
        response.raise_for_status()
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(response.content)
            tmp_path = tmp_file.name
        
        text = ""
        # Method 1: PyMuPDF (fast extraction)
        with fitz.open(tmp_path) as doc:
            text = "".join([page.get_text() for page in doc])
        
        # Fallback to OCR if text is missing (scanned PDFs)
        if len(text.strip()) < 100:
            images = convert_from_path(tmp_path)
            text = "".join([pytesseract.image_to_string(img) for img in images])
        
        # Fallback to pdfplumber (complex layouts)
        if len(text.strip()) < 100:
            with pdfplumber.open(tmp_path) as pdf:
                text = "\n".join([page.extract_text() or "" for page in pdf.pages])
        
        return text.strip()
    
    except Exception as e:
        return f"Error: {str(e)}"
    
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)  # Clean up

@app.route('/extract', methods=['POST'])
def handle_request():
    data = request.json
    file_url = data.get('file_url')
    if not file_url:
        return jsonify({"error": "Missing file_url"}), 400
    extracted_text = extract_text(file_url)
    return jsonify({"text": extracted_text})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)