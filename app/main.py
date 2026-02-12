"""
FastAPI Main Application for Cloud-Native AI Service

This module handles all API routing and application lifecycle.
All AI/ML logic is delegated to the inference module.

Architecture:
- Clean separation between API layer (this file) and inference layer
- Swagger UI enabled at /docs
- Health endpoint at /health
- Query endpoint at /query
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import inference module (AI logic is separated)
from app.inference import get_pipeline, run_inference
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================
# Request/Response Models (Pydantic)
# ============================================

class QueryRequest(BaseModel):
    """
    Request model for the /query endpoint.
    
    Attributes:
        query: The user's question or search query
        k: Number of documents to retrieve (optional, default 3)
    """
    query: str = Field(
        ..., 
        min_length=1, 
        max_length=1000,
        description="The user's question or search query",
        examples=["What is machine learning?"]
    )
    k: int = Field(
        default=3, 
        ge=1, 
        le=10,
        description="Number of documents to retrieve"
    )


class QueryResponse(BaseModel):
    """
    Response model for the /query endpoint.
    
    Attributes:
        answer: The generated answer
        query: Original query for reference
        retrieved_documents: List of retrieved document snippets
        similarity_scores: Similarity scores for each document
        latency_ms: Total inference latency in milliseconds
        status: Response status
    """
    answer: str
    query: str
    retrieved_documents: list[str]
    similarity_scores: list[float]
    latency_ms: float
    status: str


class HealthResponse(BaseModel):
    """
    Response model for the /health endpoint.
    
    Attributes:
        status: Service status (healthy/unhealthy)
        timestamp: Current server timestamp
        version: API version
        model_loaded: Whether the ML model is loaded
        documents_indexed: Number of documents in the index
    """
    status: str
    timestamp: float
    version: str
    model_loaded: bool
    documents_indexed: int


class ErrorResponse(BaseModel):
    """
    Error response model.
    
    Attributes:
        error: Error type
        message: Detailed error message
        timestamp: When the error occurred
    """
    error: str
    message: str
    timestamp: float


# ============================================
# Application Lifecycle Management
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    
    This handles:
    - Startup: Initialize the ML model and index
    - Shutdown: Cleanup resources (if needed)
    
    Using lifespan is the modern FastAPI way to handle startup/shutdown.
    """
    # Startup
    logger.info("=" * 50)
    logger.info("Starting Cloud-Native AI Service...")
    logger.info("=" * 50)
    
    start_time = time.time()
    
    try:
        # Initialize the pipeline (loads model and indexes documents)
        pipeline = get_pipeline()
        logger.info(f"Pipeline initialized. Documents indexed: {pipeline.index.index.ntotal}")
    except Exception as e:
        logger.error(f"Failed to initialize pipeline: {e}")
        raise
    
    init_time = (time.time() - start_time) * 1000
    logger.info(f"Startup completed in {init_time:.2f}ms")
    logger.info("API is ready to accept requests")
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("Shutting down Cloud-Native AI Service...")


# ============================================
# FastAPI Application Instance
# ============================================

app = FastAPI(
    title="Cloud-Native AI Inference Service",
    description="""
    A production-style AI inference service with:
    
    - **FAISS Vector Search**: Fast similarity search over document embeddings
    - **RAG Pipeline**: Retrieval-Augmented Generation for intelligent responses
    - **Docker Ready**: Containerized for easy deployment
    - **Production Features**: Logging, latency tracking, health checks
    
    ## Endpoints
    
    - **GET /health**: Check service health status
    - **POST /query**: Submit a query and get an AI-powered response
    
    ## Architecture
    
    This service follows a clean architecture with separation of concerns:
    - API Layer (main.py): Handles routing, validation, and responses
    - Inference Layer (inference.py): Handles all AI/ML operations
    """,
    version="1.0.0",
    docs_url="/docs",  # Swagger UI at /docs
    redoc_url="/redoc",  # ReDoc at /redoc
    lifespan=lifespan
)

# Add CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# API Routes
# ============================================

@app.get(
    "/health", 
    response_model=HealthResponse,
    tags=["Health"],
    summary="Check service health",
    description="""
    Returns the current health status of the service.
    
    This endpoint is useful for:
    - Monitoring systems (Kubernetes probes, load balancers)
    - Debugging service availability
    - Checking if the ML model is loaded
    """
)
async def health_check():
    """
    Health check endpoint.
    
    Returns service status, model state, and indexed document count.
    This is useful for monitoring and debugging.
    """
    try:
        pipeline = get_pipeline()
        model_loaded = pipeline.is_ready()
        documents_indexed = pipeline.index.index.ntotal
        
        status = "healthy" if model_loaded else "degraded"
        
        return HealthResponse(
            status=status,
            timestamp=time.time(),
            version="1.0.0",
            model_loaded=model_loaded,
            documents_indexed=documents_indexed
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            timestamp=time.time(),
            version="1.0.0",
            model_loaded=False,
            documents_indexed=0
        )


@app.post(
    "/query",
    response_model=QueryResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid query"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    tags=["Inference"],
    summary="Submit a query for AI-powered response",
    description="""
    Submit a query and receive an AI-powered response based on 
    semantic search over the knowledge base.
    
    The query is processed through a RAG (Retrieval-Augmented Generation) pipeline:
    
    1. **Embedding**: Convert query to vector representation
    2. **Retrieval**: Find most similar documents using FAISS
    3. **Generation**: Construct answer from retrieved context
    
    Response includes:
    - Generated answer
    - Retrieved document snippets
    - Similarity scores
    - Latency measurement
    """
)
async def query_endpoint(request: QueryRequest):
    """
    Query endpoint for AI inference.
    
    Accepts a user query and returns an AI-generated response
    based on semantic search over indexed documents.
    """
    logger.info(f"Received query: '{request.query[:50]}...' (k={request.k})")
    
    try:
        # Delegate to inference module
        result = run_inference(request.query, request.k)
        
        logger.info(f"Query processed successfully. Latency: {result['latency_ms']}ms")
        
        return QueryResponse(**result)
    
    except ValueError as e:
        logger.warning(f"Invalid query: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "ValidationError",
                "message": str(e),
                "timestamp": time.time()
            }
        )
    
    except Exception as e:
        logger.error(f"Query processing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InferenceError",
                "message": "An error occurred while processing your query",
                "timestamp": time.time()
            }
        )


@app.get(
    "/",
    tags=["Root"],
    summary="API root",
    description="Returns basic API information and available endpoints."
)
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "service": "Cloud-Native AI Inference Service",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "query": "/query (POST)"
    }


# ============================================
# Entry Point (for direct execution)
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    # Run the server with uvicorn
    # This is useful for local development
    # In production, use: uvicorn app.main:app --host 0.0.0.0 --port 8000
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on file changes (development only)
        log_level="info"
    )
