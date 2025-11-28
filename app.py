from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import shutil
from database import generate_data_store
from query_data import query_rag
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Configuration
UPLOAD_FOLDER = 'data'
ALLOWED_EXTENSIONS = {'cpp', 'py', 'java', 'js', 'ts', 'html', 'css', 'txt', 'md', 'pdf', 'zip'}
MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32MB

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class QueryRequest(BaseModel):
    query: str

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file part")
    
    if file.filename == '':
        raise HTTPException(status_code=400, detail="No selected file")
    
    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        generate_data_store()
        return {"message": "File uploaded and processed successfully"}
    except Exception as e:
        # Clean up if something goes wrong? Maybe.
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/query")
async def query(request: QueryRequest):
    query_text = request.query
    if not query_text:
        raise HTTPException(status_code=400, detail="No query provided")
    
    try:
        response = query_rag(query_text)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)