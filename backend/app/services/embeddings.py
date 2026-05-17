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
        model="llama-3.1-8b-instant",
        messages=messages
    )
    return response.choices[0].message.content

def get_chat_response_stream(messages: list):
    stream = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        stream=True
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta

def generate_metadata(text: str) -> dict:
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You are a document analyzer. Respond ONLY with valid JSON, no other text."
            },
            {
                "role": "user",
                "content": f"""Analyze this document and return a JSON object with exactly these fields:
{{
  "title": "document title (max 10 words)",
  "summary": "brief summary (max 50 words)",
  "tags": ["tag1", "tag2", "tag3"]
}}

Document:
{text[:2000]}"""
            }
        ]
    )
    
    import json
    raw = response.choices[0].message.content.strip()
    return json.loads(raw)