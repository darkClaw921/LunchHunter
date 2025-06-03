from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.keyboards import get_start_keyboard, get_city_selection_keyboard
from app.database.database import Database

router = Router()
db = Database()

class UserStates(StatesGroup):
    waiting_for_city = State()

@router.message(Command("start", "help"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start и /help"""
    # Получаем город пользователя
    user_id = message.from_user.id
    city = await db.get_user_city(user_id)
    
    if city:
        # Если город уже выбран, показываем главное меню
        text = (
            f"🍽️ *Добро пожаловать в LunchHunter!*\n\n"
            f"Ваш город: *{city}*\n\n"
            "Этот бот поможет вам найти заведения с бизнес-ланчами и другими предложениями.\n\n"
            "Выберите одну из опций ниже:"
        )
        await message.answer(text, reply_markup=get_start_keyboard(), parse_mode="Markdown")
    else:
        # Если город не выбран, предлагаем выбрать
        text = (
            "🍽️ *Добро пожаловать в LunchHunter!*\n\n"
            "Для начала работы, пожалуйста, выберите ваш город:"
        )
        await message.answer(text, reply_markup=get_city_selection_keyboard(), parse_mode="Markdown")
        await state.set_state(UserStates.waiting_for_city)

@router.callback_query(F.data.startswith("city:"))
async def callback_select_city(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора города"""
    city = callback.data.split(":")[1]
    user_id = callback.from_user.id
    username = callback.from_user.username
    
    # Сохраняем выбор города в базе данных
    await db.add_user(user_id, username, city)
    
    text = (
        f"🍽️ *Добро пожаловать в LunchHunter!*\n\n"
        f"Ваш город: *{city}*\n\n"
        "Этот бот поможет вам найти заведения с бизнес-ланчами и другими предложениями.\n\n"
        "Выберите одну из опций ниже:"
    )
    await callback.message.edit_text(text, reply_markup=get_start_keyboard(), parse_mode="Markdown")
    await callback.answer(f"Город установлен: {city}")
    await state.clear()

@router.callback_query(F.data == "change_city")
async def callback_change_city(callback: CallbackQuery, state: FSMContext):
    """Обработчик изменения города"""
    text = "Пожалуйста, выберите ваш город:"
    await callback.message.edit_text(text, reply_markup=get_city_selection_keyboard())
    await callback.answer()
    await state.set_state(UserStates.waiting_for_city)

@router.callback_query(F.data == "start")
async def callback_start(callback: CallbackQuery):
    """Обработчик кнопки 'Главное меню'"""
    # Получаем город пользователя
    user_id = callback.from_user.id
    city = await db.get_user_city(user_id)
    
    text = (
        "🍽️ *Главное меню*\n\n"
        f"Ваш город: *{city}*\n\n"
        "Выберите одну из опций ниже:"
    )
    await callback.message.edit_text(text, reply_markup=get_start_keyboard(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "pagination_info")
async def callback_pagination_info(callback: CallbackQuery):
    """Обработчик нажатия на номер страницы в пагинации"""
    await callback.answer("Текущая страница")

@router.message()
async def unknown_message(message: Message):
    """Обработчик неизвестных сообщений"""
    text = (
        "Я вас не понимаю. Пожалуйста, воспользуйтесь командой /start "
        "или кнопками для взаимодействия с ботом."
    )
    await message.answer(text, reply_markup=get_start_keyboard()) 