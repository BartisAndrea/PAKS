from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.document import Document, DocumentChunk
from app.services.embeddings import chunk_text, get_embedding
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
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() or ""
    
    if not text.strip():
        raise HTTPException(status_code=400, detail="A PDF nem tartalmaz olvasható szöveget!")
    
    document = Document(
        id=uuid.uuid4(),
        filename=file.filename,
        content=text
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    chunks = chunk_text(text)
    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        doc_chunk = DocumentChunk(
            id=uuid.uuid4(),
            document_id=document.id,
            content=chunk,
            embedding=embedding,
            chunk_index=str(i)
        )
        db.add(doc_chunk)
    
    db.commit()
    
    return {
        "message": "Sikeres feltöltés!",
        "document_id": str(document.id),
        "filename": document.filename,
        "characters": len(text),
        "chunks": len(chunks)
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