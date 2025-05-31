from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from app.keyboards import get_start_keyboard

router = Router()

@router.message(Command("start", "help"))
async def cmd_start(message: Message):
    """Обработчик команды /start и /help"""
    text = (
        "🍽️ *Добро пожаловать в LunchHunter!*\n\n"
        "Этот бот поможет вам найти заведения с бизнес-ланчами и другими предложениями.\n\n"
        "Выберите одну из опций ниже:"
    )
    await message.answer(text, reply_markup=get_start_keyboard(), parse_mode="Markdown")

@router.callback_query(F.data == "start")
async def callback_start(callback: CallbackQuery):
    """Обработчик кнопки 'Главное меню'"""
    text = (
        "🍽️ *Главное меню*\n\n"
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