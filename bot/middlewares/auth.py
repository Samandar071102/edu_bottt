from aiogram import types
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import User, UserRole
from database.session import get_session
from utils.config import Config

class AuthMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        # Skip auth for start command and admin login
        if isinstance(event, types.Message) and event.text in ['/start', '/admin']:
            return await handler(event, data)
        
        # Get user from DB
        user = None
        async with get_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == event.from_user.id)
            )
            user = result.scalar_one_or_none()
        
        # Check if user exists
        if not user:
            if isinstance(event, types.Message):
                await event.answer(
                    "Siz ro'yxatdan o'tmagansiz. /start buyrug'ini bosing."
                )
            return
        
        # Check if user is blocked
        if user.is_blocked:
            if isinstance(event, types.Message):
                await event.answer("Sizning hisobingiz bloklangan.")
            return
        
        # Add user to data
        data['user'] = user
        data['role'] = user.role
        
        return await handler(event, data)