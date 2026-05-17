from groq import Groq
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks

def get_embedding(text: str) -> list[float]:
    embedding = embedding_model.encode(text)
    return embedding.tolist()

def get_chat_response(messages: list) -> str:
    response = groq_client.chat.completions.create(
        model="llama3-8b-8192",
        messages=messages
    )
    return response.choices[0].message.content