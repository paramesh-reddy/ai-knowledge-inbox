"""Chat and RAG API endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_chat_repo, get_rag_service
from app.db.repositories.chat_repo import ChatRepository
from app.db.schemas.chat import (
    AskQuestionRequest,
    AskQuestionResponse,
    ChatMessageResponse,
    ChatSessionResponse,
    CitationItem,
)
from app.services.rag_service import RAGService

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/ask", response_model=AskQuestionResponse)
async def ask_question(
    payload: AskQuestionRequest,
    chat_repo: ChatRepository = Depends(get_chat_repo),
    rag_service: RAGService = Depends(get_rag_service),
):
    """
    Executes grounded RAG question answering:
    - Generates query embedding
    - Retrieves top matching chunks from vector storage
    - Grounded generation with Gemini
    - Saves question, answer, and validated source citations to chat session
    """
    question = payload.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty.",
        )

    # Resolve or create chat session
    session_id = payload.session_id
    if session_id:
        existing_session = await chat_repo.get_session(session_id)
        if not existing_session:
            new_session = await chat_repo.create_session(title=question[:40] + ("..." if len(question) > 40 else ""))
            session_id = new_session.id
    else:
        new_session = await chat_repo.create_session(title=question[:40] + ("..." if len(question) > 40 else ""))
        session_id = new_session.id

    # 1. Record user question
    user_msg = await chat_repo.add_message(session_id=session_id, role="user", content=question)

    # 2. Run grounded RAG
    answer, citations, has_evidence = await rag_service.answer_question(
        question=question,
        top_k=payload.top_k,
    )

    # 3. Record assistant answer with validated citations
    citations_data = [c.model_dump() for c in citations]
    assistant_msg = await chat_repo.add_message(
        session_id=session_id,
        role="assistant",
        content=answer,
        citations=citations_data,
    )

    return AskQuestionResponse(
        session_id=session_id,
        user_message_id=user_msg.id,
        assistant_message_id=assistant_msg.id,
        answer=answer,
        citations=citations,
        has_evidence=has_evidence,
    )


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def list_chat_sessions(
    chat_repo: ChatRepository = Depends(get_chat_repo),
):
    """Lists recent conversation sessions with message counts."""
    sessions_with_count = await chat_repo.list_sessions(limit=30)
    return [
        ChatSessionResponse(
            id=s.id,
            title=s.title,
            created_at=s.created_at,
            message_count=count,
        )
        for s, count in sessions_with_count
    ]


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_session_messages(
    session_id: str,
    chat_repo: ChatRepository = Depends(get_chat_repo),
):
    """Retrieves all messages with citation metadata for a session."""
    session_obj = await chat_repo.get_session(session_id)
    if not session_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session '{session_id}' not found.",
        )

    messages = await chat_repo.get_session_messages(session_id)
    return [
        ChatMessageResponse(
            id=m.id,
            session_id=m.session_id,
            role=m.role,
            content=m.content,
            citations=[CitationItem(**c) for c in m.citations],
            created_at=m.created_at,
        )
        for m in messages
    ]
