from aiogram import types
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from locales import uz, en

class I18nMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()
        self.locales = {
            'uz': uz,
            'en': en
        }
    
    async def __call__(self, handler, event, data):
        # Get user language
        user = data.get('user')
        lang = user.language_code if user else 'uz'
        
        # Get locale module
        locale = self.locales.get(lang, self.locales['uz'])
        
        # Add locale to data
        data['_'] = locale.get_text
        data['locale'] = locale
        
        return await handler(event, data)