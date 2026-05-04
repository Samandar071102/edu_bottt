import sqlite3
import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryContextStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# --- 1. SOZLAMALAR ---
API_TOKEN = 'SIZNING_BOT_TOKENINGIZ'
ADMINS = [123456789]  # O'zingizning Telegram ID raqamingizni yozing

logging.basicConfig(level=logging.INFO)
storage = MemoryContextStorage()
bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.MARKDOWN)
dp = Dispatcher(bot, storage=storage)

# --- 2. MA'LUMOTLAR BAZASI FUNKSIYALARI ---
def db_init():
    conn = sqlite3.connect('texnikum.db')
    cur = conn.cursor()
    # Guruhlar
    cur.execute("CREATE TABLE IF NOT EXISTS groups(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)")
    # Foydalanuvchilar
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY, full_name TEXT, group_id INTEGER, 
        FOREIGN KEY(group_id) REFERENCES groups(id))""")
    # Mavzular
    cur.execute("CREATE TABLE IF NOT EXISTS subjects(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, group_id INTEGER)")
    # Materiallar
    cur.execute("CREATE TABLE IF NOT EXISTS materials(id INTEGER PRIMARY KEY AUTOINCREMENT, subject_id INTEGER, file_id TEXT, file_type TEXT)")
    
    # Namuna uchun guruhlar qo'shish
    groups = [('911-guruh',), ('912-guruh',), ('913-guruh',)]
    cur.executemany("INSERT OR IGNORE INTO groups (name) VALUES (?)", groups)
    
    conn.commit()
    conn.close()

# --- 3. HOLATLAR (STATES) ---
class Registration(StatesGroup):
    waiting_for_name = State()
    waiting_for_group = State()

class AdminStates(StatesGroup):
    waiting_for_group_selection = State()
    waiting_for_subject_name = State()
    waiting_for_file = State()

# --- 4. O'QUVCHI HANDLERLARI (START & RO'YXATDAN O'TISH) ---
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    conn = sqlite3.connect('texnikum.db')
    cur = conn.cursor()
    user = cur.execute("SELECT full_name FROM users WHERE user_id = ?", (message.from_user.id,)).fetchone()
    conn.close()

    if user:
        await message.answer(f"Xush kelibsiz, *{user[0]}*!\n\nDarslarni ko'rish uchun quyidagi buyruqdan foydalaning:\n/mavzular")
    else:
        await message.answer("Assalomu alaykum! Texnikum botiga xush kelibsiz.\nRo'yxatdan o'tish uchun to'liq ismingizni kiriting:")
        await Registration.waiting_for_name.set()

@dp.message_handler(state=Registration.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    
    conn = sqlite3.connect('texnikum.db')
    cur = conn.cursor()
    groups = cur.execute("SELECT name FROM groups").fetchall()
    conn.close()

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for g in groups:
        keyboard.add(types.KeyboardButton(g[0]))

    await message.answer("Guruhingizni tanlang:", reply_markup=keyboard)
    await Registration.waiting_for_group.set()

@dp.message_handler(state=Registration.waiting_for_group)
async def process_group(message: types.Message, state: FSMContext):
    data = await state.get_data()
    group_name = message.text

    conn = sqlite3.connect('texnikum.db')
    cur = conn.cursor()
    group_res = cur.execute("SELECT id FROM groups WHERE name = ?", (group_name,)).fetchone()

    if group_res:
        cur.execute("INSERT INTO users (user_id, full_name, group_id) VALUES (?, ?, ?)",
                    (message.from_user.id, data['full_name'], group_res[0]))
        conn.commit()
        await message.answer(f"Muvaffaqiyatli ro'yxatdan o'tdingiz!\n\nEndi darslarni ko'rish uchun /mavzular buyrug'ini bosing.", reply_markup=types.ReplyKeyboardRemove())
        await state.finish()
    else:
        await message.answer("Iltimos, tugmalar orqali guruhingizni tanlang.")
    conn.close()

# --- 5. ADMIN PANEL HANDLERLARI ---
@dp.message_handler(commands=['admin'], user_id=ADMINS)
async def admin_start(message: types.Message):
    conn = sqlite3.connect('texnikum.db')
    cur = conn.cursor()
    groups = cur.execute("SELECT name FROM groups").fetchall()
    conn.close()

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for g in groups:
        keyboard.insert(types.InlineKeyboardButton(text=f"📁 {g[0]}", callback_data=f"adm_g_{g[0]}"))
    
    await message.answer("🛠 *Admin Panel*\nQaysi guruhga material qo'shmoqchisiz?", reply_markup=keyboard)
    await AdminStates.waiting_for_group_selection.set()

@dp.callback_query_handler(lambda c: c.data.startswith('adm_g_'), state=AdminStates.waiting_for_group_selection)
async def admin_group_chosen(callback: types.CallbackQuery, state: FSMContext):
    group_name = callback.data.replace('adm_g_', '')
    await state.update_data(chosen_group=group_name)
    await bot.send_message(callback.from_user.id, f"Tanlangan guruh: *{group_name}*\nEndi dars mavzusini yozing:")
    await AdminStates.waiting_for_subject_name.set()
    await callback.answer()

@dp.message_handler(state=AdminStates.waiting_for_subject_name)
async def admin_subject_step(message: types.Message, state: FSMContext):
    await state.update_data(sub_name=message.text)
    await message.answer(f"Mavzu: *{message.text}*\nEndi faylni yuboring:")
    await AdminStates.waiting_for_file.set()

@dp.message_handler(content_types=['document', 'video', 'photo'], state=AdminStates.waiting_for_file)
async def admin_file_step(message: types.Message, state: FSMContext):
    data = await state.get_data()
    file_id = message.document.file_id if message.document else (message.video.file_id if message.video else message.photo[-1].file_id)
    f_type = "doc" if message.document else ("video" if message.video else "photo")

    conn = sqlite3.connect('texnikum.db')
    cur = conn.cursor()
    g_id = cur.execute("SELECT id FROM groups WHERE name = ?", (data['chosen_group'],)).fetchone()[0]
    cur.execute("INSERT INTO subjects (title, group_id) VALUES (?, ?)", (data['sub_name'], g_id))
    cur.execute("INSERT INTO materials (subject_id, file_id, file_type) VALUES (?, ?, ?)", (cur.lastrowid, file_id, f_type))
    conn.commit()
    conn.close()

    await message.answer("✅ Material yuklandi!")
    await state.finish()

# --- 6. MAVZULARNI KO'RISH (O'QUVCHILAR UCHUN) ---
@dp.message_handler(commands=['mavzular'])
async def list_subjects(message: types.Message):
    conn = sqlite3.connect('texnikum.db')
    cur = conn.cursor()
    user = cur.execute("SELECT group_id FROM users WHERE user_id = ?", (message.from_user.id,)).fetchone()
    
    if user:
        subjects = cur.execute("SELECT id, title FROM subjects WHERE group_id = ?", (user[0],)).fetchall()
        if subjects:
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            for s in subjects:
                keyboard.add(types.InlineKeyboardButton(text=s[1], callback_data=f"get_f_{s[0]}"))
            await message.answer("Sizning guruhingiz uchun mavzular:", reply_markup=keyboard)
        else:
            await message.answer("Hozircha mavzular yuklanmagan.")
    else:
        await message.answer("Avval ro'yxatdan o'ting: /start")
    conn.close()

@dp.callback_query_handler(lambda c: c.data.startswith('get_f_'))
async def send_material(callback: types.CallbackQuery):
    sub_id = callback.data.replace('get_f_', '')
    conn = sqlite3.connect('texnikum.db')
    cur = conn.cursor()
    file = cur.execute("SELECT file_id, file_type FROM materials WHERE subject_id = ?", (sub_id,)).fetchone()
    conn.close()

    if file:
        if file[1] == "doc": await callback.message.answer_document(file[0])
        elif file[1] == "video": await callback.message.answer_video(file[0])
        else: await callback.message.answer_photo(file[0])
    await callback.answer()

# --- 7. ISHGA TUSHIRISH ---
if __name__ == '__main__':
    db_init()
    executor.start_polling(dp, skip_updates=True)
