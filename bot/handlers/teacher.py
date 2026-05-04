from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from database.session import get_session
from database.models import Lesson, Subject, Category, File
from bot.keyboards.teacher import get_subjects_keyboard, get_categories_keyboard
from services.file_service import save_file, validate_file
from utils.states import LessonStates

router = Router()

class LessonStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_content = State()
    waiting_for_summary = State()
    waiting_for_objectives = State()
    waiting_for_keywords = State()
    waiting_for_files = State()
    waiting_for_subject = State()
    waiting_for_category = State()
    waiting_for_schedule = State()

@router.message(F.text == "➕ Dars qo'shish")
async def add_lesson_start(message: types.Message, state: FSMContext, _):
    """Start lesson creation process"""
    await message.answer(_("enter_lesson_title"))
    await state.set_state(LessonStates.waiting_for_title)

@router.message(LessonStates.waiting_for_title)
async def process_title(message: types.Message, state: FSMContext, _):
    """Process lesson title"""
    await state.update_data(title=message.text)
    await message.answer(_("enter_lesson_content"))
    await state.set_state(LessonStates.waiting_for_content)

@router.message(LessonStates.waiting_for_content)
async def process_content(message: types.Message, state: FSMContext, _):
    """Process lesson content"""
    await state.update_data(content=message.text)
    await message.answer(_("enter_lesson_summary"))
    await state.set_state(LessonStates.waiting_for_summary)

@router.message(LessonStates.waiting_for_summary)
async def process_summary(message: types.Message, state: FSMContext, _):
    """Process lesson summary"""
    await state.update_data(summary=message.text)
    await message.answer(_("enter_lesson_objectives"))
    await state.set_state(LessonStates.waiting_for_objectives)

@router.message(LessonStates.waiting_for_objectives)
async def process_objectives(message: types.Message, state: FSMContext, _):
    """Process lesson objectives"""
    await state.update_data(objectives=message.text)
    await message.answer(_("enter_keywords_comma_separated"))
    await state.set_state(LessonStates.waiting_for_keywords)

@router.message(LessonStates.waiting_for_keywords)
async def process_keywords(message: types.Message, state: FSMContext, _):
    """Process keywords"""
    keywords = [k.strip() for k in message.text.split(",")]
    await state.update_data(keywords=keywords)
    
    # Get subjects
    async with get_session() as session:
        subjects = await session.execute(select(Subject).where(Subject.is_active == True))
        subjects = subjects.scalars().all()
    
    await message.answer(
        _("select_subject"),
        reply_markup=get_subjects_keyboard(subjects)
    )
    await state.set_state(LessonStates.waiting_for_subject)

@router.callback_query(F.data.startswith("subject_"), LessonStates.waiting_for_subject)
async def process_subject(callback: types.CallbackQuery, state: FSMContext, _):
    """Process subject selection"""
    subject_id = int(callback.data.split("_")[1])
    await state.update_data(subject_id=subject_id)
    
    # Get categories for this subject
    async with get_session() as session:
        categories = await session.execute(
            select(Category).where(
                Category.subject_id == subject_id,
                Category.parent_id.is_(None)
            )
        )
        categories = categories.scalars().all()
    
    await callback.message.edit_text(
        _("select_category"),
        reply_markup=get_categories_keyboard(categories)
    )
    await state.set_state(LessonStates.waiting_for_category)

@router.message(LessonStates.waiting_for_files, F.document | F.photo | F.audio | F.video)
async def process_files(message: types.Message, state: FSMContext, _):
    """Process file uploads"""
    data = await state.get_data()
    files = data.get("files", [])
    
    # Validate file
    is_valid, error_msg = validate_file(message)
    if not is_valid:
        await message.answer(error_msg)
        return
    
    # Save file
    file_info = await save_file(message, message.from_user.id)
    files.append(file_info)
    
    await state.update_data(files=files)
    await message.answer(
        _("file_added", count=len(files)),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text=_("finish_adding"), callback_data="finish_files")]
        ])
    )

@router.callback_query(F.data == "finish_files", LessonStates.waiting_for_files)
async def finish_files(callback: types.CallbackQuery, state: FSMContext, _):
    """Finish file uploads and create lesson"""
    data = await state.get_data()
    
    async with get_session() as session:
        # Create lesson
        lesson = Lesson(
            title=data['title'],
            content=data['content'],
            summary=data['summary'],
            objectives=data['objectives'],
            keywords=data['keywords'],
            subject_id=data['subject_id'],
            category_id=data.get('category_id'),
            created_by=callback.from_user.id,
            is_published=False  # Requires admin approval or auto-publish
        )
        session.add(lesson)
        await session.flush()
        
        # Add files
        for file_data in data.get('files', []):
            file = File(
                lesson_id=lesson.id,
                **file_data
            )
            session.add(file)
        
        await session.commit()
    
    await callback.message.edit_text(_("lesson_created_successfully"))
    await state.clear()