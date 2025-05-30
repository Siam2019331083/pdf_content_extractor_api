# main.py
from fastapi import FastAPI, Request
import fitz  # PyMuPDF
import requests
import io

app = FastAPI()

@app.post("/extract-pdf")
async def extract_pdf(request: Request):
    data = await request.json()
    url = data.get("url")
    try:
        response = requests.get(url)
        pdf_stream = io.BytesIO(response.content)
        doc = fitz.open(stream=pdf_stream, filetype="pdf")
        full_text = "\n\n".join([page.get_text() for page in doc])
        return {"url": url, "text": full_text}
    except Exception as e:
        return {"url": url, "error": str(e)}
