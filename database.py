import argparse
import os
import shutil
import zipfile
import tempfile
import time
from pathlib import Path
from langchain_community.document_loaders import PyPDFDirectoryLoader, TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from embedding_function import embedding_function
from langchain_chroma import Chroma

CHROMA_PATH = "chroma"
DATA_PATH = "data"
TEMP_PATH = "temp_extracted"

def extract_zip(zip_path: str, extract_path: str) -> None:
    """Extract zip file to temporary directory."""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)

def load_documents():
    documents = []
    
    # Load PDFs
    pdf_loader = PyPDFDirectoryLoader(DATA_PATH)
    try:
        documents.extend(pdf_loader.load())
        
        # --- ADD THIS DEBUG CHECK ---
        if len(documents) > 0:
            print(f"📄 DEBUG: Loaded PDF with {len(documents[0].page_content)} characters.")
            print(f"📄 DEBUG PREVIEW: {documents[0].page_content[:100]}...") # Show first 100 chars
        else:
            print("⚠️ DEBUG: PDF loaded but no documents found!")
        # ----------------------------

    except Exception as e:
        print(f"Error loading PDFs: {e}")

    # Create DirectoryLoader for regular files in DATA_PATH
    regular_loader = DirectoryLoader(
        DATA_PATH,
        glob="**/*.*",
        exclude=["**/*.zip", "**/*.pdf"],
        loader_cls=lambda file_path: TextLoader(file_path, encoding='utf-8'),
        show_progress=True
    )
    documents.extend(regular_loader.load())

    zip_files = list(Path(DATA_PATH).glob("**/*.zip"))
    if zip_files:
        
        os.makedirs(TEMP_PATH, exist_ok=True)
        
        for zip_file in zip_files:
            temp_dir = os.path.join(TEMP_PATH, zip_file.stem)
            os.makedirs(temp_dir, exist_ok=True)
            
            extract_zip(str(zip_file), temp_dir)
            
            zip_loader = DirectoryLoader(
                temp_dir,
                glob="**/*.*",
                loader_cls=lambda file_path: TextLoader(file_path, encoding='utf-8'),
                show_progress=True
            )
            try:
                zip_documents = zip_loader.load()
                documents.extend(zip_documents)
            except Exception as e:
                print(f"Error loading documents from {zip_file}: {e}")

    return documents

def clean_temp_files():
    """Clean up temporary extracted files."""
    if os.path.exists(TEMP_PATH):
        shutil.rmtree(TEMP_PATH)

def split_documents(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,       # 1500 is a sweet spot for both code and text
        chunk_overlap=300,     # Higher overlap prevents cutting code functions in half
        length_function=len,
        # Prioritize splitting by paragraphs, then code blocks, then lines
        separators=["\n\n", "\n", " ", ""], 
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)

def add_to_chroma(chunks: list[Document]):
    db = Chroma(
        persist_directory=CHROMA_PATH, embedding_function=embedding_function()
    )

    chunks_with_ids = calculate_chunk_ids(chunks)

    existing_items = db.get(include=[]) 
    existing_ids = set(existing_items["ids"])
    print(f"Number of existing documents in DB: {len(existing_ids)}")

    new_chunks = []
    for chunk in chunks_with_ids:
        if chunk.metadata["id"] not in existing_ids:
            new_chunks.append(chunk)

    if len(new_chunks):
        print(f"👉 Adding new documents: {len(new_chunks)}")
        batch_size = 10 
        for i in range(0, len(new_chunks), batch_size):
            batch = new_chunks[i:i + batch_size]
            print(f"Processing batch {i//batch_size + 1} of {(len(new_chunks)-1)//batch_size + 1}")
            batch_ids = [chunk.metadata["id"] for chunk in batch]
            
            # Simple retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    db.add_documents(batch, ids=batch_ids)
                    break
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        print(f"Rate limit hit, waiting 20 seconds... (Attempt {attempt+1}/{max_retries})")
                        time.sleep(20)
                    else:
                        raise e
            
            time.sleep(4) # Wait 4 seconds to stay under 15 RPM limit
        print("✅ All documents added successfully")
    else:
        print("✅ No new documents to add")

def calculate_chunk_ids(chunks):

    last_page_id = None
    current_chunk_index = 0

    for chunk in chunks:
        source = chunk.metadata.get("source")
        page = chunk.metadata.get("page")
        current_page_id = f"{source}:{page}"

        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0

        chunk_id = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id

        chunk.metadata["id"] = chunk_id

    return chunks

def clear_database():
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

def generate_data_store(reset: bool = False):
    if reset:
        print("✨ Clearing Database")
        clear_database()

    try:
        documents = load_documents()
        chunks = split_documents(documents)
        add_to_chroma(chunks)
    finally:
        clean_temp_files()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Reset the database.")
    args = parser.parse_args()
    generate_data_store(args.reset)

if __name__ == "__main__":
    main()
