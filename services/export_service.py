import pandas as pd
from io import BytesIO
from sqlalchemy import select
from database.session import get_session
from database.models import User, Lesson, Submission, Grade

class ExportService:
    @staticmethod
    async def export_users_to_csv() -> BytesIO:
        """Export all users to CSV"""
        async with get_session() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()
            
            data = []
            for user in users:
                data.append({
                    "ID": user.id,
                    "Telegram ID": user.telegram_id,
                    "Username": user.username,
                    "Full Name": user.full_name,
                    "Role": user.role.value,
                    "Is Active": user.is_active,
                    "Is Blocked": user.is_blocked,
                    "Created At": user.created_at
                })
            
            df = pd.DataFrame(data)
            output = BytesIO()
            df.to_csv(output, index=False, encoding='utf-8-sig')
            output.seek(0)
            return output
    
    @staticmethod
    async def export_lessons_to_excel() -> BytesIO:
        """Export lessons to Excel"""
        async with get_session() as session:
            result = await session.execute(
                select(Lesson).order_by(Lesson.created_at.desc())
            )
            lessons = result.scalars().all()
            
            data = []
            for lesson in lessons:
                data.append({
                    "ID": lesson.id,
                    "Title": lesson.title,
                    "Subject": lesson.subject.name if lesson.subject else "",
                    "Category": lesson.category.name if lesson.category else "",
                    "Created By": lesson.creator.full_name,
                    "Is Published": lesson.is_published,
                    "Created At": lesson.created_at
                })
            
            df = pd.DataFrame(data)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Lessons', index=False)
            output.seek(0)
            return output