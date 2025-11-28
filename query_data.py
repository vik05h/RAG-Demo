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
PROMPT_TEMPLATE = """
You are a helpful AI assistant. You are analyzing a document provided by the user.

Context from the document:
{context}

---

User Question: {question}

Instructions:
1. If the user asks about "the resume", "this file", or "the candidate", assume the Context above is what they are referring to.
2. Summarize the details if asked generally.
3. If the answer is truly not present, say "I don't have that information."
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