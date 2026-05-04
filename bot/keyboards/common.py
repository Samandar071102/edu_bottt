from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_main_menu(role: str) -> ReplyKeyboardMarkup:
    """Get main menu based on user role"""
    builder = ReplyKeyboardBuilder()
    
    if role == "admin":
        builder.row(
            KeyboardButton(text="👥 Foydalanuvchilar"),
            KeyboardButton(text="📊 Statistika")
        )
        builder.row(
            KeyboardButton(text="📚 Fanlar"),
            KeyboardButton(text="📢 E'lonlar")
        )
        builder.row(
            KeyboardButton(text="⚙️ Sozlamalar"),
            KeyboardButton(text="📥 Export")
        )
    elif role == "teacher":
        builder.row(
            KeyboardButton(text="➕ Dars qo'shish"),
            KeyboardButton(text="📝 Test yaratish")
        )
        builder.row(
            KeyboardButton(text="📂 Mening darslarim"),
            KeyboardButton(text="📋 Topshiriqlar")
        )
        builder.row(
            KeyboardButton(text="📊 Progress"),
            KeyboardButton(text="⚙️ Sozlamalar")
        )
    elif role == "student":
        builder.row(
            KeyboardButton(text="📚 Fanlar"),
            KeyboardButton(text="📝 Darslar")
        )
        builder.row(
            KeyboardButton(text="📋 Topshiriqlar"),
            KeyboardButton(text="📊 Progress")
        )
        builder.row(
            KeyboardButton(text="⭐ Sevimlilar"),
            KeyboardButton(text="❓ Savol")
        )
    
    builder.row(KeyboardButton(text="🔙 Asosiy menyu"))
    return builder.as_markup(resize_keyboard=True)