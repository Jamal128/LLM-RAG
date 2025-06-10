# rag_component.py

import os
from docx import Document
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer, util
import torch # Necesario para util.cos_sim de sentence_transformers

# --- Configuración ---
KNOWLEDGE_BASE_PATH = "knowledge"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K_DOCUMENTS = 3 # Número de documentos más relevantes a recuperar

# Modelo de embeddings (puedes cambiarlo si quieres otro, pero este es bueno y ligero)
# 'all-MiniLM-L6-v2' es un buen modelo de embeddings para texto.
EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2')

# Base de datos en memoria: Lista de diccionarios, cada uno con 'text' y 'embedding'
document_chunks = []

# --- Funciones de Procesamiento de Documentos ---

def load_document_text(filepath):
    """Carga el texto de un archivo PDF o DOCX."""
    text = ""
    if filepath.endswith(".pdf"):
        try:
            reader = PdfReader(filepath)
            for page in reader.pages:
                text += page.extract_text() or ""
        except Exception as e:
            print(f"Error al leer PDF {filepath}: {e}")
            return None
    elif filepath.endswith(".docx"):
        try:
            doc = Document(filepath)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            print(f"Error al leer DOCX {filepath}: {e}")
            return None
    # Añade aquí más tipos de archivo si necesitas (ej. .txt)
    elif filepath.endswith(".txt"):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            print(f"Error al leer TXT {filepath}: {e}")
            return None
    else:
        print(f"Formato de archivo no soportado o desconocido: {filepath}")
        return None
    return text

def chunk_text(text):
    """Divide el texto en chunks."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_text(text)

def initialize_rag_database():
    """
    Carga, divide y embebe todos los documentos en la carpeta de conocimiento.
    Se ejecuta una vez al inicio de la aplicación.
    """
    global document_chunks
    document_chunks = [] # Limpiar por si se llama más de una vez
    
    print(f"Inicializando base de datos RAG desde: {KNOWLEDGE_BASE_PATH}")
    if not os.path.exists(KNOWLEDGE_BASE_PATH):
        print(f"ADVERTENCIA: La carpeta '{KNOWLEDGE_BASE_PATH}' no existe. No se cargarán documentos RAG.")
        return

    for filename in os.listdir(KNOWLEDGE_BASE_PATH):
        filepath = os.path.join(KNOWLEDGE_BASE_PATH, filename)
        if os.path.isfile(filepath):
            print(f"Procesando documento: {filename}")
            text_content = load_document_text(filepath)
            if text_content:
                chunks = chunk_text(text_content)
                print(f"  - Dividido en {len(chunks)} chunks.")
                chunk_embeddings = EMBEDDING_MODEL.encode(chunks, convert_to_tensor=True)
                for i, chunk in enumerate(chunks):
                    document_chunks.append({
                        "text": chunk,
                        "embedding": chunk_embeddings[i],
                        "source": filename # Para saber de qué documento viene el chunk
                    })
    print(f"RAG: Base de datos inicializada con {len(document_chunks)} chunks.")
    if not document_chunks:
        print("RAG: No se cargaron documentos. Asegúrate de que la carpeta 'knowledge' contiene archivos soportados y que no están vacíos.")


def retrieve_documents(query):
    """
    Embebe la consulta y recupera los chunks más relevantes de la base de conocimiento.
    """
    if not document_chunks:
        print("ADVERTENCIA RAG: No hay documentos cargados en la base de datos.")
        return ["No se encontraron documentos relevantes en la base de conocimiento."]

    query_embedding = EMBEDDING_MODEL.encode(query, convert_to_tensor=True)

    # Calcular similitud coseno entre la consulta y todos los chunks
    # Asegúrate de que query_embedding y document_chunks[i]['embedding'] tengan el mismo dtype (float32)
    # y estén en el mismo dispositivo (CPU en este caso)
    similarities = util.cos_sim(query_embedding, torch.stack([d['embedding'] for d in document_chunks]))

    # Obtener los índices de los chunks más similares
    top_k_indices = torch.topk(similarities, k=min(TOP_K_DOCUMENTS, len(document_chunks)), dim=1).indices[0]

    retrieved_content = []
    for idx in top_k_indices:
        retrieved_content.append(
            f"--- Fuente: {document_chunks[idx]['source']} ---\n"
            f"{document_chunks[idx]['text']}"
        )
    
    return retrieved_content

# Ejecutar la inicialización de la base de datos RAG cuando este módulo se importa
if __name__ == '__main__':
    # Esto se ejecutará si corres 'python rag_component.py' directamente
    # Útil para probar la carga de documentos de forma independiente.
    initialize_rag_database()
    print("\n--- Prueba de recuperación ---")
    test_query = "¿Qué es el link building?"
    results = retrieve_documents(test_query)
    for res in results:
        print(f"\n{res}")
else:
    # Esto se ejecutará cuando app.py importe rag_component
    initialize_rag_database()