from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.document import DocumentChunk
from app.services.embeddings import chunk_text, get_embedding, generate_metadata
import uuid

@celery_app.task
def process_document(document_id: str, text: str, filename: str):
    db = SessionLocal()
    try:
        from app.models.document import Document
        from sqlalchemy.dialects.postgresql import UUID
        import uuid as uuid_module
        
        doc = db.query(Document).filter(
            Document.id == uuid_module.UUID(document_id)
        ).first()
        
        if not doc:
            return {"error": "Document not found"}
        
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            embedding = get_embedding(chunk)
            doc_chunk = DocumentChunk(
                id=uuid.uuid4(),
                document_id=doc.id,
                content=chunk,
                embedding=embedding,
                chunk_index=str(i)
            )
            db.add(doc_chunk)
        
        db.commit()

        try:
            metadata = generate_metadata(text)
            doc.summary = metadata.get("summary", "")
            doc.tags = ", ".join(metadata.get("tags", []))
            db.commit()
        except Exception:
            pass

        return {"status": "done", "chunks": len(chunks)}
    
    finally:
        db.close()