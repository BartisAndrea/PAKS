from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text as sql_text
from app.database import get_db
from app.models.document import Document, DocumentChunk
from app.services.embeddings import chunk_text, get_embedding, get_chat_response, get_chat_response_stream, generate_metadata
import pypdf
import io
import uuid

router = APIRouter()

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Csak PDF fájl tölthető fel!")
    
    content = await file.read()
    
    pdf_reader = pypdf.PdfReader(io.BytesIO(content))
    extracted_text = ""
    for page in pdf_reader.pages:
        extracted_text += page.extract_text() or ""
    
    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="A PDF nem tartalmaz olvasható szöveget!")
    
    document = Document(
        id=uuid.uuid4(),
        filename=file.filename,
        content=extracted_text,
        summary="Feldolgozás alatt...",
        tags=""
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    from app.services.tasks import process_document
    process_document.delay(str(document.id), extracted_text, file.filename)

    return {
        "message": "Feltöltés sikeres, feldolgozás folyamatban!",
        "document_id": str(document.id),
        "filename": document.filename,
        "characters": len(extracted_text),
        "status": "processing"
    }

@router.get("/documents")
def list_documents(db: Session = Depends(get_db)):
    documents = db.query(Document).all()
    return [
        {
            "id": str(doc.id),
            "filename": doc.filename,
            "created_at": str(doc.created_at)
        }
        for doc in documents
    ]

@router.get("/search")
def search_documents(q: str, db: Session = Depends(get_db)):
    if not q:
        raise HTTPException(status_code=400, detail="Keresési kifejezés szükséges!")
    
    query_embedding = get_embedding(q)
    
    results = db.execute(
        sql_text("""
            SELECT dc.content, dc.document_id, d.filename,
                   1 - (dc.embedding <=> CAST(:embedding AS vector)) as similarity
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            ORDER BY dc.embedding <=> CAST(:embedding AS vector)
            LIMIT 5
        """),
        {"embedding": str(query_embedding)}
    ).fetchall()
    
    return [
        {
            "content": row[0],
            "document_id": str(row[1]),
            "filename": row[2],
            "similarity": float(row[3])
        }
        for row in results
    ]

@router.post("/chat")
async def chat(request: dict, db: Session = Depends(get_db)):
    question = request.get("question", "")
    if not question:
        raise HTTPException(status_code=400, detail="Kérdés szükséges!")
    
    query_embedding = get_embedding(question)
    
    results = db.execute(
        sql_text("""
            SELECT dc.content, d.filename
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            ORDER BY dc.embedding <=> CAST(:embedding AS vector)
            LIMIT 3
        """),
        {"embedding": str(query_embedding)}
    ).fetchall()
    
    context = "\n\n".join([f"[{row[1]}]: {row[0]}" for row in results])
    
    messages = [
        {
            "role": "system",
            "content": "Te egy személyes tudásrendszer asszisztense vagy. Csak a megadott kontextus alapján válaszolj. Ha nem találod a választ a kontextusban, mondd meg hogy nem tudod."
        },
        {
            "role": "user",
            "content": f"Kontextus:\n{context}\n\nKérdés: {question}"
        }
    ]
    
    response = get_chat_response(messages)
    
    return {
        "question": question,
        "answer": response,
        "sources": [row[1] for row in results]
    }

@router.post("/chat/stream")
async def chat_stream(request: dict, db: Session = Depends(get_db)):
    question = request.get("question", "")
    if not question:
        raise HTTPException(status_code=400, detail="Kérdés szükséges!")
    
    query_embedding = get_embedding(question)
    
    results = db.execute(
        sql_text("""
            SELECT dc.content, d.filename
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            ORDER BY dc.embedding <=> CAST(:embedding AS vector)
            LIMIT 3
        """),
        {"embedding": str(query_embedding)}
    ).fetchall()
    
    context = "\n\n".join([f"[{row[1]}]: {row[0]}" for row in results])
    
    messages = [
        {
            "role": "system",
            "content": "Te egy személyes tudásrendszer asszisztense vagy. Csak a megadott kontextus alapján válaszolj. Ha nem találod a választ a kontextusban, mondd meg hogy nem tudod."
        },
        {
            "role": "user",
            "content": f"Kontextus:\n{context}\n\nKérdés: {question}"
        }
    ]
    
    return StreamingResponse(
        get_chat_response_stream(messages),
        media_type="text/plain"
    )