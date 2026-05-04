from datetime import datetime, timedelta
from sqlalchemy import select, and_
from database.session import get_session
from database.models import Notification, Homework, User
from aiogram import Bot
import asyncio

class NotificationService:
    def __init__(self, bot: Bot):
        self.bot = bot
    
    async def check_deadlines(self):
        """Check for upcoming homework deadlines and send reminders"""
        while True:
            try:
                async with get_session() as session:
                    # Get homework due in next 24 hours
                    tomorrow = datetime.utcnow() + timedelta(days=1)
                    homeworks = await session.execute(
                        select(Homework).where(
                            and_(
                                Homework.due_date >= datetime.utcnow(),
                                Homework.due_date <= tomorrow
                            )
                        )
                    )
                    homeworks = homeworks.scalars().all()
                    
                    for hw in homeworks:
                        # Get students in the subject
                        # This is simplified - you'd need to get students enrolled in the subject
                        students = await session.execute(
                            select(User).where(User.role == "student")
                        )
                        students = students.scalars().all()
                        
                        for student in students:
                            # Check if notification already sent
                            existing = await session.execute(
                                select(Notification).where(
                                    and_(
                                        Notification.user_id == student.id,
                                        Notification.notification_type == "deadline",
                                        Notification.message.contains(f"Homework ID: {hw.id}")
                                    )
                                )
                            )
                            
                            if not existing.scalar_one_or_none():
                                notification = Notification(
                                    user_id=student.id,
                                    message=f"⏰ E'tibor bering! '{hw.title}' topshirig'i {hw.due_date.strftime('%d.%m.%Y %H:%M')} da tugaydi",
                                    notification_type="deadline"
                                )
                                session.add(notification)
                                await session.commit()
                                
                                # Send Telegram message
                                try:
                                    await self.bot.send_message(
                                        chat_id=student.telegram_id,
                                        text=notification.message
                                    )
                                except Exception as e:
                                    print(f"Failed to send notification to {student.telegram_id}: {e}")
            
            except Exception as e:
                print(f"Error in deadline checker: {e}")
            
            await asyncio.sleep(3600)  # Check every hour