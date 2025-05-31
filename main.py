from fastapi import FastAPI, Request
import fitz
import httpx
import io
import asyncio
from concurrent.futures import ProcessPoolExecutor

app = FastAPI()
executor = ProcessPoolExecutor()

async def fetch_pdf_bytes(url):
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content
    except Exception as e:
        raise RuntimeError(f"Download error: {str(e)}")

def extract_text_from_pdf_bytes(pdf_bytes):
    try:
        pdf_stream = io.BytesIO(pdf_bytes)
        doc = fitz.open(stream=pdf_stream, filetype="pdf")
        text = "\n\n".join([page.get_text("text") for page in doc])
        return text
    except Exception as e:
        raise RuntimeError(f"Parsing error: {str(e)}")

@app.post("/extract-pdf")
async def extract_pdf(request: Request):
    data = await request.json()
    url = data.get("url", "").strip()

    if not url:
        return {"error": "No PDF URL provided."}

    try:
        pdf_bytes = await fetch_pdf_bytes(url)
        loop = asyncio.get_event_loop()
        text = await asyncio.wait_for(
            loop.run_in_executor(executor, extract_text_from_pdf_bytes, pdf_bytes),
            timeout=15
        )
        return {"url": url, "text": text}
    except Exception as e:
        return {"url": url, "error": str(e)}
