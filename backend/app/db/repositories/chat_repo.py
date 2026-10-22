"""Chat repository for sessions and message persistence."""
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.chat import ChatSession, ChatMessage


class ChatRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_session(self, title: str = "New Chat") -> ChatSession:
        chat_session = ChatSession(title=title)
        self.session.add(chat_session)
        await self.session.commit()
        await self.session.refresh(chat_session)
        return chat_session

    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        query = select(ChatSession).where(ChatSession.id == session_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_sessions(self, limit: int = 20) -> List[Tuple[ChatSession, int]]:
        """Returns sessions with message count."""
        query = (
            select(ChatSession, func.count(ChatMessage.id).label("msg_count"))
            .outerjoin(ChatMessage, ChatMessage.session_id == ChatSession.id)
            .group_by(ChatSession.id)
            .order_by(desc(ChatSession.created_at))
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.all())

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        citations: Optional[List[Dict[str, Any]]] = None,
    ) -> ChatMessage:
        msg = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
        )
        if citations:
            msg.citations = citations
        self.session.add(msg)
        await self.session.commit()
        await self.session.refresh(msg)
        return msg

    async def get_session_messages(self, session_id: str) -> List[ChatMessage]:
        query = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_session_title(self, session_id: str, title: str) -> None:
        session_obj = await self.get_session(session_id)
        if session_obj:
            session_obj.title = title[:255]
            await self.session.commit()
