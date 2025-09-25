import os
from docx import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import fitz  # PyMuPDF

# Make sure you have the necessary libraries installed
# pip install python-docx langchain langchain-community sentence-transformers chromadb

# --- Step 1: Document Processing for Multiple Files ---
def extract_text_from_pdf(file_path):
    """Extracts text from a single PDF file."""
    text = ""
    try:
        # Open the PDF file
        with fitz.open(file_path) as doc:
            # Iterate through each page and extract text
            for page in doc:
                text += page.get_text()
        print(f"Successfully extracted text from: {os.path.basename(file_path)}")
        return text
    except Exception as e:
        print(f"Error extracting text from {os.path.basename(file_path)}: {e}")
        return None
    
def extract_text_from_multiple_docx(directory_path):
    """Extracts text from all .docx and .pdf files in a given directory."""
    full_text = ""
    if not os.path.isdir(directory_path):
        print(f"Error: Directory not found at {directory_path}")
        return None

    # Iterate through all files in the specified directory
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if filename.endswith(".docx"):    
            try:
                doc = Document(file_path)
                for para in doc.paragraphs:
                    full_text += para.text + "\n"
                print(f"Successfully extracted text from: {filename}")
            except Exception as e:
                print(f"Error extracting text from {filename}: {e}")
        elif filename.endswith(".pdf"):
            pdf_text = extract_text_from_pdf(file_path)
            if pdf_text:
                full_text += pdf_text + "\n"        
    return full_text if full_text else None

# --- Step 2: Chunking ---
def chunk_text(text, chunk_size=1000, chunk_overlap=200):
    """Splits a large text document into smaller, overlapping chunks."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len
    )
    return text_splitter.split_text(text)

# --- Step 3: Embedding and Storing ---
def embed_and_store_chunks(chunks, persist_directory="./rag_db"):
    """
    Converts text chunks into vector embeddings and stores them in a
    local vector database (ChromaDB).
    """
    embeddings_model = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    vector_store = Chroma.from_texts(
        texts=chunks,
        embedding=embeddings_model,
        persist_directory=persist_directory
    )
    
    vector_store.persist()
    print(f"Successfully embedded and stored {len(chunks)} chunks.")
    return vector_store

# --- Main Execution ---
if __name__ == "__main__":
    # Define the path to your data directory
    data_dir = os.path.join(os.path.dirname(__file__), '../data')
    
    # 1. Extract text from all DOCX files in the data directory
    raw_text = extract_text_from_multiple_docx(data_dir)
    
    if raw_text:
        # 2. Split the combined text into manageable chunks
        text_chunks = chunk_text(raw_text)
        
        # 3. Embed the chunks and store them in a vector database
        db = embed_and_store_chunks(text_chunks)
        print("RAG knowledge base for all documents built successfully!")
    else:
        print("No text was extracted. Please check the data directory and file formats.")