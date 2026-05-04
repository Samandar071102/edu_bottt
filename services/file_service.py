import os
from typing import Tuple, Optional
from aiogram.types import Message, Document, PhotoSize, Audio, Video
from aiogram import Bot
from utils.config import Config

class FileService:
    ALLOWED_EXTENSIONS = {
        'pdf', 'docx', 'pptx', 'txt', 
        'jpg', 'jpeg', 'png', 'gif',
        'mp3', 'mp4', 'm4a'
    }
    
    MAX_FILE_SIZE = Config.MAX_FILE_SIZE_MB * 1024 * 1024  # Convert to bytes
    
    @staticmethod
    async def validate_file(message: Message) -> Tuple[bool, str]:
        """Validate uploaded file"""
        file = None
        file_name = ""
        file_size = 0
        
        if message.document:
            file = message.document
            file_name = file.file_name
            file_size = file.file_size
        elif message.photo:
            file = message.photo[-1]  # Get largest photo
            file_name = f"photo_{file.file_unique_id}.jpg"
            file_size = file.file_size
        elif message.audio:
            file = message.audio
            file_name = file.file_name or f"audio_{file.file_unique_id}.mp3"
            file_size = file.file_size
        elif message.video:
            file = message.video
            file_name = file.file_name or f"video_{file.file_unique_id}.mp4"
            file_size = file.file_size
        
        if not file:
            return False, "Fayl topilmadi"
        
        # Check file size
        if file_size > FileService.MAX_FILE_SIZE:
            return False, f"Fayl hajmi {Config.MAX_FILE_SIZE_MB}MB dan katta bo'lmasligi kerak"
        
        # Check file extension
        ext = file_name.split('.')[-1].lower() if '.' in file_name else ''
        if ext not in FileService.ALLOWED_EXTENSIONS:
            return False, f"'{ext}' kengaytmali fayllar ruxsat etilmaydi"
        
        return True, "OK"
    
    @staticmethod
    async def save_file(message: Message, user_id: int) -> dict:
        """Save file and return metadata"""
        file = None
        file_type = ""
        file_name = ""
        
        if message.document:
            file = message.document
            file_type = file.file_name.split('.')[-1].lower()
            file_name = file.file_name
        elif message.photo:
            file = message.photo[-1]
            file_type = "jpg"
            file_name = f"photo_{file.file_unique_id}.jpg"
        elif message.audio:
            file = message.audio
            file_type = "mp3"
            file_name = file.file_name or f"audio_{file.file_unique_id}.mp3"
        elif message.video:
            file = message.video
            file_type = "mp4"
            file_name = file.file_name or f"video_{file.file_unique_id}.mp4"
        
        # Download file
        bot = message.bot
        file_path = f"uploads/{user_id}/{file_name}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        await bot.download(file, destination=file_path)
        
        return {
            "file_id": file.file_id,
            "file_type": file_type,
            "file_name": file_name,
            "file_size": file.file_size,
            "mime_type": getattr(file, 'mime_type', None),
            "local_path": file_path
        }
    
    @staticmethod
    async def get_file_info(bot: Bot, file_id: str) -> Optional[dict]:
        """Get file info from Telegram"""
        try:
            file = await bot.get_file(file_id)
            return {
                "file_path": file.file_path,
                "file_url": f"https://api.telegram.org/file/bot{Config.BOT_TOKEN}/{file.file_path}"
            }
        except Exception as e:
            return None