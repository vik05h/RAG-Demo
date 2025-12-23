import argparse
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
from embedding_function import embedding_function

load_dotenv()

CHROMA_PATH = "chroma"

# --- UPDATED PROMPT ---
# This prompts the model to be a helpful assistant rather than just a fact-checker.
# query_data.py

# --- UPDATE THIS PROMPT ---
PROMPT_TEMPLATE = """
You are a versatile AI assistant capable of analyzing any uploaded file (Code, PDF, Resume, or Text).

Context from the uploaded file:
{context}

---

User Question: {question}

Instructions:
1. **Analyze the Context:** First, determine if the context is a Resume, a Source Code file, or an Academic Document.
2. **If it is a Resume:** Act as a recruiter. Summarize skills, experience, and projects.
3. **If it is Source Code:** Act as a Senior Developer. Explain what the code does, look for bugs if asked, and format any code output in Markdown.
4. **If it is a Lecture/PDF:** Act as a Tutor. Explain the concepts clearly.
5. **Knowledge Rule:** Use the Context above as your primary source of truth. However, if the answer is not explicitly in the context, **you may use your general knowledge** to answer the question helpfully. If you use outside knowledge, please mention, "This information is based on general knowledge, not the file."
"""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query_text", type=str, help="The query text.")
    args = parser.parse_args()
    query_text = args.query_text
    query_rag(query_text)


def query_rag(query_text: str):
    get_embedding_function = embedding_function()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=get_embedding_function)

    # Search for top 5 most relevant chunks (k=10 can sometimes be too noisy)
    results = db.similarity_search_with_score(query_text, k=5)

    if not results:
        print("No results found in database.")
        return "I couldn't find any information in the uploaded documents."

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)

    # --- ADD THIS DEBUG PRINT ---
    print("\n--- DEBUG: WHAT THE AI SEES ---")
    print(context_text)
    print("-------------------------------\n")

    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.3
    )
    
    response_text = model.invoke(prompt).content

    sources = [doc.metadata.get("id", None) for doc, _score in results]
    formatted_response = f"Response: {response_text}\nSources: {sources}"
    print(formatted_response)
    return response_text


if __name__ == "__main__":
    main()