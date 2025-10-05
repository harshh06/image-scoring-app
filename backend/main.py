# backend/main.py
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from typing import List

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Image Scoring Backend!"}

@app.post("/upload-pdf/")
async def upload_pdf(pdf_file: UploadFile = File(...)):
    # In a real app, you'd process the PDF here
    return {"filename": pdf_file.filename, "content_type": pdf_file.content_type, "message": "PDF received!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)