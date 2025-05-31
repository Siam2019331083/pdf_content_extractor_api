# main.py
from fastapi import FastAPI, Request
import fitz  # PyMuPDF
import httpx
import io
import asyncio
from concurrent.futures import ThreadPoolExecutor

app = FastAPI()
executor = ThreadPoolExecutor()

async def fetch_pdf(url):
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return url, response.content
    except Exception as e:
        return url, f"Download error: {str(e)}"

def extract_text_from_pdf(url, pdf_bytes):
    try:
        pdf_stream = io.BytesIO(pdf_bytes)
        doc = fitz.open(stream=pdf_stream, filetype="pdf")
        full_text = "\n\n".join([page.get_text() for page in doc])
        return {"url": url, "text": full_text}
    except Exception as e:
        return {"url": url, "error": f"Parsing error: {str(e)}"}

@app.post("/extract-multiple-pdfs")
async def extract_multiple_pdfs(request: Request):
    data = await request.json()
    urls_csv = data.get("urls", "")
    urls = [u.strip() for u in urls_csv.split(",") if u.strip()]

    downloads = await asyncio.gather(*[fetch_pdf(url) for url in urls])

    loop = asyncio.get_event_loop()
    tasks = [
        loop.run_in_executor(executor, extract_text_from_pdf, url, content)
        for url, content in downloads
        if not isinstance(content, str)
    ]

    results = await asyncio.gather(*tasks)

    # Include errors
    for url, content in downloads:
        if isinstance(content, str):
            results.append({"url": url, "error": content})

    return results
