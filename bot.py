import sqlite3
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryContextStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# --- 1. SOZLAMALAR ---
API_TOKEN = '8381553106:AAF0NR0LexDkerLAm6yDcmXZ3x7w2i_t4ig'
ADMINS = [8208777595]  # O'zingizning Telegram ID raqamingiz

logging.basicConfig(level=logging.INFO)
storage = MemoryContextStorage()
bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.MARKDOWN)
dp = Dispatcher(bot, storage=storage)

# --- 2. MA'LUMOTLAR BAZASI FUNKSIYALARI ---
def db_init():
    conn = sqlite3.connect('texnikum.db')
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS groups(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)")
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY, full_name TEXT, group_id INTEGER, score INTEGER DEFAULT 0,
        FOREIGN KEY(group_id) REFERENCES groups(id))""")
    cur.execute("CREATE TABLE IF NOT EXISTS subjects(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, group_id INTEGER)")
    cur.execute("CREATE TABLE IF NOT EXISTS materials(id INTEGER PRIMARY KEY AUTOINCREMENT, subject_id INTEGER, file_id TEXT, file_type TEXT)")
    cur.execute("""CREATE TABLE IF NOT EXISTS quizzes(
        id INTEGER PRIMARY KEY AUTOINCREMENT, subject_id INTEGER, question TEXT, 
        options TEXT, correct_option TEXT, FOREIGN KEY(subject_id) REFERENCES subjects(id))""")
    
    # Namuna guruhlar
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
    waiting_for_broadcast = State()

class UserStates(StatesGroup):
    waiting_for_question = State()

# --- 4. KLAVIATURALAR (KEYBOARDS) ---
def get_main_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("📚 Mavzular", "🏆 Reyting")
    keyboard.add("❓ Savol berish")
    return keyboard

# --- 5. START VA RO'YXATDAN O'TISH ---
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    conn = sqlite3.connect('texnikum.db')
    cur = conn.cursor()
    user = cur.execute("SELECT full_name FROM users WHERE user_id = ?", (message.from_user.id,)).fetchone()
    conn.close()

    if user:
        await message.answer(f"Xush kelibsiz, *{user[0]}*!", reply_markup=get_main_menu())
    else:
        await message.answer("Assalomu alaykum! Texnikum botiga xush kelibsiz.\nTo'liq ismingizni kiriting:")
        await Registration.waiting_for_name.set()

@dp.message_handler(state=Registration.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    conn = sqlite3.connect('texnikum.db')
    cur = conn.cursor()
    groups = cur.execute("SELECT name FROM groups").fetchall()
    conn.close()

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for g in groups: keyboard.add(types.KeyboardButton(g[0]))
    await message.answer("Guruhingizni tanlang:", reply_markup=keyboard)
    await Registration.waiting_for_group.set()

@dp.message_handler(state=Registration.waiting_for_group)
async def process_group(message: types.Message, state: FSMContext):
    data = await state.get_data()
    conn = sqlite3.connect('texnikum.db')
    cur = conn.cursor()
    g_res = cur.execute("SELECT id FROM groups WHERE name = ?", (message.text,)).fetchone()
    if g_res:
        cur.execute("INSERT INTO users (user_id, full_name, group_id) VALUES (?, ?, ?)",
                    (message.from_user.id, data['full_name'], g_res[0]))
        conn.commit()
        await message.answer("✅ Ro'yxatdan o'tdingiz!", reply_markup=get_main_menu())
        await state.finish()
    else:
        await message.answer("Guruhni tugmalar orqali tanlang.")
    conn.close()

# --- 6. ADMIN PANEL (YUKLASH VA RASSILKA) ---
@dp.message_handler(commands=['admin'], user_id=ADMINS)
async def admin_start(message: types.Message):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("📤 Material yuklash", callback_data="adm_upload"))
    kb.add(types.InlineKeyboardButton("📢 Hammaga xabar yuborish", callback_data="adm_broadcast"))
    await message.answer("🛠 *Admin Paneli:* Bo'limni tanlang:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "adm_upload", user_id=ADMINS)
async def start_upload(callback: types.CallbackQuery):
    conn = sqlite3.connect('texnikum.db')
    cur = conn.cursor()
    groups = cur.execute("SELECT name FROM groups").fetchall()
    conn.close()
    kb = types.InlineKeyboardMarkup()
    for g in groups: kb.add(types.InlineKeyboardButton(text=g[0], callback_data=f"adm_g_{g[0]}"))
    await callback.message.edit_text("Guruhni tanlang:", reply_markup=kb)
    await AdminStates.waiting_for_group_selection.set()

@dp.callback_query_handler(lambda c: c.data.startswith('adm_g_'), state=AdminStates.waiting_for_group_selection)
async def adm_g_chosen(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(chosen_group=callback.data.replace('adm_g_', ''))
    await bot.send_message(callback.from_user.id, "Mavzu nomini yozing:")
    await AdminStates.waiting_for_subject_name.set()
    await callback.answer()

@dp.message_handler(state=AdminStates.waiting_for_subject_name)
async def adm_sub_name(message: types.Message, state: FSMContext):
    await state.update_data(sub_name=message.text)
    await message.answer("Faylni yuboring:")
    await AdminStates.waiting_for_file.set()

@dp.message_handler(content_types=['document', 'video', 'photo'], state=AdminStates.waiting_for_file)
async def adm_file_save(message: types.Message, state: FSMContext):
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
    await message.answer("✅ Yuklandi!")
    await state.finish()

# RASSILKA QISMI
@dp.callback_query_handler(lambda c: c.data == "adm_broadcast", user_id=ADMINS)
async def broadcast_prompt(callback: types.CallbackQuery):
    await callback.message.answer("Barcha o'quvchilarga yubormoqchi bo'lgan xabaringizni yozing:")
    await AdminStates.waiting_for_broadcast.set()
    await callback.answer()

@dp.message_handler(state=AdminStates.waiting_for_broadcast)
async def send_broadcast(message: types.Message, state: FSMContext):
    conn = sqlite3.connect('texnikum.db')
    cur = conn.cursor()
    users = cur.execute("SELECT user_id FROM users").fetchall()
    conn.close()
    count = 0
    for u in users:
        try:
            await bot.send_message(u[0], f"📢 **MUHIM XABAR!**\n\n{message.text}")
            count += 1
        except: pass
    await message.answer(f"✅ Xabar {count} ta foydalanuvchiga yuborildi.")
    await state.finish()

# --- 7. O'QUVCHI: MAVZULAR, TEST VA SAVOL ---
@dp.message_handler(lambda m: m.text == "📚 Mavzular")
async def list_subjects(message: types.Message):
    conn = sqlite3.connect('texnikum.db')
    cur = conn.cursor()
    u = cur.execute("SELECT group_id FROM users WHERE user_id = ?", (message.from_user.id,)).fetchone()
    if u:
        subs = cur.execute("SELECT id, title FROM subjects WHERE group_id = ?", (u[0],)).fetchall()
        kb = types.InlineKeyboardMarkup(row_width=1)
        for s in subs: kb.add(types.InlineKeyboardButton(text=s[1], callback_data=f"get_f_{s[0]}"))
        await message.answer("📚 Guruhingizga tegishli mavzular:", reply_markup=kb)
    else: await message.answer("/start orqali ro'yxatdan o'ting.")
    conn.close()

@dp.callback_query_handler(lambda c: c.data.startswith('get_f_'))
async def send_file(callback: types.CallbackQuery):
    s_id = callback.data.replace('get_f_', '')
    conn = sqlite3.connect('texnikum.db')
    cur = conn.cursor()
    f = cur.execute("SELECT file_id, file_type FROM materials WHERE subject_id = ?", (s_id,)).fetchone()
    conn.close()
    if f:
        if f[1] == "doc": await callback.message.answer_document(f[0])
        elif f[1] == "video": await callback.message.answer_video(f[0])
        else: await callback.message.answer_photo(f[0])
        await callback.message.answer("Darsni o'rganib chiqib, bilimingizni sinab ko'ring.")
    await callback.answer()

@dp.message_handler(lambda m: m.text == "🏆 Reyting")
async def show_rating(message: types.Message):
    conn = sqlite3.connect('texnikum.db')
    cur = conn.cursor()
    users = cur.execute("SELECT u.full_name, u.score FROM users u ORDER BY u.score DESC LIMIT 10").fetchall()
    conn.close()
    res = "🏆 *Top 10 O'quvchi:*\n\n"
    for i, u in enumerate(users, 1): res += f"{i}. {u[0]} — {u[1]} ball\n"
    await message.answer(res)

@dp.message_handler(lambda m: m.text == "❓ Savol berish")
async def ask_question(message: types.Message):
    await message.answer("Savolingizni yozing, o'qituvchi tez orada javob beradi:")
    await UserStates.waiting_for_question.set()

@dp.message_handler(state=UserStates.waiting_for_question)
async def forward_question(message: types.Message, state: FSMContext):
    for admin in ADMINS:
        await bot.send_message(admin, f"📩 **Yangi savol!**\nKimdan: {message.from_user.full_name}\nID: {message.from_user.id}\n\nSavol: {message.text}")
    await message.answer("✅ Savolingiz o'qituvchiga yuborildi.")
    await state.finish()

if __name__ == '__main__':
    db_init()
    executor.start_polling(dp, skip_updates=True)
