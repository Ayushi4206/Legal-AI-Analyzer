from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import tempfile
import json
from datetime import datetime
from typing import List, Optional
import asyncio

# Import our custom modules
from document_processor import DocumentProcessor
from ai_analyzer import AIAnalyzer
from entity_extractor import EntityExtractor
from risk_analyzer import RiskAnalyzer

app = FastAPI(
    title="Legal Document Analyzer API",
    description="AI-powered legal document analysis and risk assessment",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize processors
document_processor = DocumentProcessor()
ai_analyzer = AIAnalyzer()
entity_extractor = EntityExtractor()
risk_analyzer = RiskAnalyzer()

# In-memory storage for demo (use database in production)
documents_store = {}

@app.get("/")
async def root():
    return {"message": "Legal Document Analyzer API", "version": "1.0.0"}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a legal document
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith(('.pdf', '.docx', '.doc')):
            raise HTTPException(
                status_code=400, 
                detail="Unsupported file type. Please upload PDF, DOCX, or DOC files."
            )
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Process document
            document_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(documents_store)}"
            
            # Extract text from document
            extracted_text = document_processor.extract_text(tmp_file_path)
            
            # Analyze document with AI
            analysis_result = await ai_analyzer.analyze_document(extracted_text, file.filename)
            
            # Extract entities
            entities = entity_extractor.extract_entities(extracted_text)
            
            # Perform risk analysis
            risk_assessment = risk_analyzer.assess_risk(analysis_result['clauses'])
            
            # Combine all results
            full_analysis = {
                "document_id": document_id,
                "filename": file.filename,
                "upload_time": datetime.now().isoformat(),
                "text_content": extracted_text,
                "summary": analysis_result.get('summary', ''),
                "clauses": analysis_result.get('clauses', []),
                "entities": entities,
                "risk_assessment": risk_assessment,
                "overall_risk": risk_assessment.get('overall_risk', 'medium')
            }
            
            # Store in memory (use database in production)
            documents_store[document_id] = full_analysis
            
            return {
                "document_id": document_id,
                "status": "success",
                "message": "Document processed successfully",
                "analysis": {
                    "summary": full_analysis["summary"],
                    "clauses": full_analysis["clauses"],
                    "entities": full_analysis["entities"],
                    "overall_risk": full_analysis["overall_risk"]
                }
            }
            
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@app.get("/documents")
async def get_documents():
    """
    Get list of all uploaded documents
    """
    return {
        "documents": [
            {
                "document_id": doc_id,
                "filename": doc_data["filename"],
                "upload_time": doc_data["upload_time"],
                "overall_risk": doc_data["overall_risk"]
            }
            for doc_id, doc_data in documents_store.items()
        ]
    }

@app.get("/documents/{document_id}")
async def get_document(document_id: str):
    """
    Get detailed analysis of a specific document
    """
    if document_id not in documents_store:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return documents_store[document_id]

@app.post("/analyze/{document_id}")
async def reanalyze_document(document_id: str):
    """
    Re-analyze a document with updated AI models
    """
    if document_id not in documents_store:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc_data = documents_store[document_id]
    
    # Re-analyze with AI
    analysis_result = await ai_analyzer.analyze_document(
        doc_data["text_content"], 
        doc_data["filename"]
    )
    
    # Update stored data
    doc_data.update({
        "clauses": analysis_result.get('clauses', []),
        "summary": analysis_result.get('summary', ''),
        "last_analyzed": datetime.now().isoformat()
    })
    
    return {
        "status": "success",
        "message": "Document re-analyzed successfully",
        "analysis": {
            "summary": doc_data["summary"],
            "clauses": doc_data["clauses"],
            "entities": doc_data["entities"],
            "overall_risk": doc_data["overall_risk"]
        }
    }

@app.post("/compare")
async def compare_documents(doc1_id: str, doc2_id: str):
    """
    Compare two documents and highlight differences
    """
    if doc1_id not in documents_store or doc2_id not in documents_store:
        raise HTTPException(status_code=404, detail="One or both documents not found")
    
    doc1 = documents_store[doc1_id]
    doc2 = documents_store[doc2_id]
    
    # Perform comparison analysis
    comparison = await ai_analyzer.compare_documents(doc1, doc2)
    
    return {
        "status": "success",
        "comparison": comparison,
        "document1": {
            "id": doc1_id,
            "filename": doc1["filename"],
            "risk_level": doc1["overall_risk"]
        },
        "document2": {
            "id": doc2_id,
            "filename": doc2["filename"],
            "risk_level": doc2["overall_risk"]
        }
    }

@app.post("/qa/{document_id}")
async def ask_question(document_id: str, question: str):
    """
    Ask questions about a specific document using RAG
    """
    if document_id not in documents_store:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc_data = documents_store[document_id]
    
    # Use RAG to answer question
    answer = await ai_analyzer.answer_question(
        doc_data["text_content"],
        doc_data["clauses"],
        question
    )
    
    return {
        "status": "success",
        "question": question,
        "answer": answer,
        "document_id": document_id,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/extract-entities/{document_id}")
async def extract_entities_endpoint(document_id: str):
    """
    Extract entities from a document
    """
    if document_id not in documents_store:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc_data = documents_store[document_id]
    entities = entity_extractor.extract_entities(doc_data["text_content"])
    
    # Update stored data
    doc_data["entities"] = entities
    
    return {
        "status": "success",
        "entities": entities
    }

@app.get("/risk-analysis/{document_id}")
async def get_risk_analysis(document_id: str):
    """
    Get detailed risk analysis for a document
    """
    if document_id not in documents_store:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc_data = documents_store[document_id]
    
    return {
        "status": "success",
        "risk_analysis": doc_data.get("risk_assessment", {}),
        "overall_risk": doc_data.get("overall_risk", "medium"),
        "clauses": doc_data.get("clauses", [])
    }

@app.post("/jurisdiction-check/{document_id}")
async def check_jurisdiction(document_id: str, jurisdiction: str = "indian"):
    """
    Check document compliance with specific jurisdiction laws
    """
    if document_id not in documents_store:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc_data = documents_store[document_id]
    
    # Perform jurisdiction-specific compliance check
    compliance_result = await ai_analyzer.check_jurisdiction_compliance(
        doc_data["clauses"],
        jurisdiction
    )
    
    return {
        "status": "success",
        "jurisdiction": jurisdiction,
        "compliance_result": compliance_result,
        "document_id": document_id
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "documents_count": len(documents_store)
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)