class UzbekLocale:
    def get_text(self, key: str, **kwargs) -> str:
        texts = {
            "welcome_new_user": "Assalomu alaykum! Ta'lim botimizga xush kelibsiz. Siz talaba sifatida ro'yxatdan o'tdingiz.",
            "welcome_back": "Qaytib kelganingizdan xursandmiz, {name}!",
            "main_menu": "Asosiy menyu:",
            "enter_admin_key": "Admin parolini kiriting:",
            "enter_lesson_title": "Dars nomini kiriting:",
            "enter_lesson_content": "Dars mazmunini kiriting:",
            "enter_lesson_summary": "Qisqacha mazmunini kiriting:",
            "enter_lesson_objectives": "Dars maqsadlarini kiriting:",
            "enter_keywords_comma_separated": "Kalit so'zlarni vergul bilan ajratib kiriting:",
            "select_subject": "Fan tanlang:",
            "select_category": "Kategoriya tanlang:",
            "file_added": "Fayl qo'shildi. Jami: {count} ta fayl",
            "finish_adding": "Tugatish",
            "lesson_created_successfully": "Dars muvaffaqiyatli yaratildi! Admin tasdiqlashini kuting.",
            "file_type_not_allowed": "Bu turdagi fayl ruxsat etilmaydi",
            "file_too_large": "Fayl hajmi juda katta",
            # ... add more keys as needed
        }
        
        text = texts.get(key, key)
        return text.format(**kwargs) if kwargs else text