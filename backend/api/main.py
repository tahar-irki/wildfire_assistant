from contextlib import asynccontextmanager
from pathlib import Path
from threading import Lock
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.model.inference.model_loader import load_model
from backend.model.inference.generator import generate_answer
from backend.rag.rag import ForestFireRAG, EMBEDDINGS_FILE, PASSAGES_FILE


# =========================================================
# CONFIGURATION
# =========================================================

APP_NAME = "ForestGuard AI API"
APP_VERSION = "1.0.0"

# Only allow the local Vue development server by default.
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Number of reference passages to retrieve per question.
RAG_TOP_K = 4

# Limit generated answer length.
MAX_NEW_TOKENS = 256


# =========================================================
# APPLICATION STATE
# =========================================================

class ApplicationState:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.rag = None
        self.model_loaded = False
        self.rag_loaded = False

        # Prevent simultaneous generation calls from competing
        # for model memory, particularly on CPU.
        self.generation_lock = Lock()


state = ApplicationState()


# =========================================================
# REQUEST / RESPONSE SCHEMAS
# =========================================================

class ChatRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The user's forest-fire-related question."
    )


class SourceResponse(BaseModel):
    title: str
    page: int
    score: Optional[float] = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceResponse]
    rag_used: bool


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    rag_loaded: bool
    device: Optional[str] = None


# =========================================================
# STARTUP AND SHUTDOWN
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Load the language model and RAG system once at startup.
    """

    print("\n" + "=" * 60)
    print("STARTING FORESTGUARD AI API")
    print("=" * 60)

    # -----------------------------------------------------
    # Load fine-tuned Qwen model
    # -----------------------------------------------------

    try:
        print("\nLoading ForestGuard language model...")

        state.model, state.tokenizer = load_model()
        state.model_loaded = True

        print("Language model is ready.")

    except Exception as error:
        print("\nMODEL LOADING FAILED:")
        print(error)
        raise RuntimeError(
            "Could not load the ForestGuard language model."
        ) from error

    # -----------------------------------------------------
    # Load RAG knowledge base
    # -----------------------------------------------------

    try:
        if EMBEDDINGS_FILE.exists() and PASSAGES_FILE.exists():

            print("\nLoading ForestGuard RAG knowledge base...")

            state.rag = ForestFireRAG()
            state.rag_loaded = True

            print("RAG knowledge base is ready.")

        else:
            print("\nRAG knowledge base was not found.")
            print("The API will run without document retrieval.")
            print("Build it with: python -m backend.rag.rag --build")

    except Exception as error:
        # Do not prevent the model API from starting if RAG
        # artifacts are unavailable or invalid.
        print("\nRAG LOADING FAILED:")
        print(error)

        state.rag = None
        state.rag_loaded = False

    print("\nForestGuard API startup completed.")
    print("=" * 60 + "\n")

    yield

    # -----------------------------------------------------
    # Shutdown
    # -----------------------------------------------------

    print("\nShutting down ForestGuard API...")

    state.model = None
    state.tokenizer = None
    state.rag = None

    state.model_loaded = False
    state.rag_loaded = False


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=(
        "An AI assistant for forest-fire knowledge, "
        "prevention, safety, and environmental protection."
    ),
    lifespan=lifespan
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# =========================================================
# ROOT ENDPOINT
# =========================================================

@app.get("/")
def root():
    return {
        "message": "Welcome to ForestGuard AI API",
        "version": APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


# =========================================================
# HEALTH ENDPOINT
# =========================================================

@app.get("/health", response_model=HealthResponse)
def health_check():

    device = None

    if state.model_loaded and state.model is not None:
        device = str(next(state.model.parameters()).device)

    return HealthResponse(
        status="ready" if state.model_loaded else "not_ready",
        model_loaded=state.model_loaded,
        rag_loaded=state.rag_loaded,
        device=device
    )


# =========================================================
# CHAT ENDPOINT
# =========================================================

@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Process a user question.

    Workflow:
        1. Validate the question.
        2. Retrieve relevant PDF passages through RAG.
        3. Generate an answer using Qwen + LoRA.
        4. Return the answer and source metadata.
    """

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    if not state.model_loaded or state.model is None:
        raise HTTPException(
            status_code=503,
            detail="ForestGuard language model is not available."
        )

    context = None
    sources = []
    rag_used = False

    # -----------------------------------------------------
    # Retrieve relevant document passages
    # -----------------------------------------------------

    if state.rag_loaded and state.rag is not None:

        try:
            context, retrieved_sources = state.rag.format_context(
                question,
                top_k=RAG_TOP_K
            )

            if context.strip():

                sources = retrieved_sources
                rag_used = True

        except Exception as error:
            print(f"RAG retrieval error: {error}")

            # Continue with the fine-tuned model without
            # retrieved context if retrieval fails.
            context = None
            sources = []
            rag_used = False

    # -----------------------------------------------------
    # Generate the answer
    # -----------------------------------------------------

    try:
        with state.generation_lock:

            answer = generate_answer(
                model=state.model,
                tokenizer=state.tokenizer,
                question=question,
                context=context,
                max_new_tokens=MAX_NEW_TOKENS
            )

        if not answer:
            raise RuntimeError("The model returned an empty answer.")

    except Exception as error:
        print(f"Generation error: {error}")

        raise HTTPException(
            status_code=500,
            detail="ForestGuard could not generate an answer."
        ) from error

    # -----------------------------------------------------
    # Return response
    # -----------------------------------------------------

    return ChatResponse(
        answer=answer,
        sources=sources,
        rag_used=rag_used
    )