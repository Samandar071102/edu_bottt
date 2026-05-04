from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryContextStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import sqlite3

API_TOKEN = 'SIZNING_TOKENINGIZ'

storage = MemoryContextStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)

# Ro'yxatdan o'tish bosqichlari
class Registration(StatesGroup):
    waiting_for_name = State()
    waiting_for_group = State()

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    # Bazada bor-yo'qligini tekshirish
    conn = sqlite3.connect('texnikum.db')
    cur = conn.cursor()
    user = cur.execute("SELECT * FROM users WHERE user_id = ?", (message.from_user.id,)).fetchone()
    conn.close()

    if user:
        await message.answer(f"Xush kelibsiz, {user[1]}! Kerakli bo'limni tanlang.")
        # Bu yerda asosiy menyuni chiqarish mumkin
    else:
        await message.answer("Assalomu alaykum! Texnikum botiga xush kelibsiz.\nIltimos, to'liq ismingizni kiriting:")
        await Registration.waiting_for_name.set()

@dp.message_handler(state=Registration.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    
    # Guruhlarni bazadan olish
    conn = sqlite3.connect('texnikum.db')
    cur = conn.cursor()
    groups = cur.execute("SELECT name FROM groups").fetchall()
    conn.close()

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for g in groups:
        keyboard.add(types.KeyboardButton(g[0]))

    await message.answer("Endi guruhingizni tanlang:", reply_markup=keyboard)
    await Registration.waiting_for_group.set()

@dp.message_handler(state=Registration.waiting_for_group)
async def process_group(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    group_name = message.text

    conn = sqlite3.connect('texnikum.db')
    cur = conn.cursor()
    group_id = cur.execute("SELECT id FROM groups WHERE name = ?", (group_name,)).fetchone()

    if group_id:
        cur.execute("INSERT INTO users (user_id, full_name, group_id) VALUES (?, ?, ?)",
                    (message.from_user.id, user_data['full_name'], group_id[0]))
        conn.commit()
        await message.answer("Muvaffaqiyatli ro'yxatdan o'tdingiz!", reply_markup=types.ReplyKeyboardRemove())
    else:
        await message.answer("Xatolik! Ro'yxatdagi guruhlardan birini tanlang.")
        return

    conn.close()
    await state.finish()

if __name__ == '__main__':
    db_start()
    add_default_groups() # Test uchun
    executor.start_polling(dp, skip_updates=True)
