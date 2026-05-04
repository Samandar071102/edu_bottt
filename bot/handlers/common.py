from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command
from database.session import get_session
from database.models import User, UserRole
from bot.keyboards.common import get_main_menu

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message, user: User, _):
    """Handle /start command"""
    if user:
        await message.answer(
            _("welcome_back", name=user.full_name),
            reply_markup=get_main_menu(user.role.value)
        )
    else:
        # Register new user
        async with get_session() as session:
            new_user = User(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                full_name=message.from_user.full_name,
                role=UserRole.STUDENT  # Default role
            )
            session.add(new_user)
            await session.commit()
        
        await message.answer(
            _("welcome_new_user"),
            reply_markup=get_main_menu("student")
        )

@router.message(Command("admin"))
async def cmd_admin(message: types.Message, _):
    """Admin login with secret key"""
    await message.answer(_("enter_admin_key"))

@router.message(F.text == "🔙 Asosiy menyu")
async def cmd_main_menu(message: types.Message, user: User, _):
    """Return to main menu"""
    await message.answer(
        _("main_menu"),
        reply_markup=get_main_menu(user.role.value)
    )