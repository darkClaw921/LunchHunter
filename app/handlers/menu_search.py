from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from app.database import Database
from app.keyboards import (
    get_search_results_keyboard, 
    get_start_keyboard, 
    get_full_place_details_keyboard
)
import math

router = Router()

class MenuSearch(StatesGroup):
    waiting_for_query = State()

@router.callback_query(F.data == "menu_search")
async def callback_menu_search(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Поиск по меню'"""
    await state.set_state(MenuSearch.waiting_for_query)
    
    text = (
        "🔍 *Поиск по меню*\n\n"
        "Введите название блюда или категорию для поиска.\n"
        "Например: *карбонара*, *пиво*, *десерт* и т.д."
    )
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await callback.answer()

@router.message(StateFilter(MenuSearch.waiting_for_query))
async def process_menu_search(message: Message, state: FSMContext):
    """Обработчик ввода поискового запроса"""
    query = message.text.strip()
    
    if not query:
        await message.answer("Пожалуйста, введите корректный поисковый запрос.")
        return
    
    # Сохраняем запрос в состоянии
    await state.update_data(query=query)
    
    # Выполняем поиск
    db = Database()
    total = await db.count_search_results(query)
    
    if total == 0:
        await message.answer(
            f"По запросу *{query}* ничего не найдено. Попробуйте другой запрос.",
            reply_markup=get_start_keyboard(),
            parse_mode="Markdown"
        )
        await state.clear()
        return
    
    # Получаем первую страницу результатов
    page = 1
    per_page = 1  # Показываем по одному заведению на странице
    total_pages = math.ceil(total / per_page)
    offset = (page - 1) * per_page
    
    places = await db.search_places_by_menu(query, limit=per_page, offset=offset)
    
    if not places:
        await message.answer(
            "К сожалению, произошла ошибка при получении данных.",
            reply_markup=get_start_keyboard()
        )
        await state.clear()
        return
    
    place = places[0]
    place_id = place['id']
    
    # Получаем позиции меню для заведения, соответствующие запросу
    menu_items = await db.get_menu_items_by_place_id(place_id)
    matching_items = [item for item in menu_items if query.lower() in item['name'].lower() or query.lower() in item['category'].lower()]
    
    # Получаем отзывы
    reviews = await db.get_reviews_by_place_id(place_id)
    
    # Формируем полный текст с информацией о заведении
    text = f"🔍 *Результаты поиска по запросу:* {query}\n\n"
    text += f"*{place['name']}*\n"
    text += f"📍 *Адрес:* {place['address']}\n\n"
    
    # Показываем найденные позиции меню
    text += f"*Найденные позиции меню:*\n"
    for item in matching_items[:3]:  # Показываем только первые 3 позиции
        text += f"• {item['name']} - {item['price']} руб. ({item['category']})\n"
    
    if len(matching_items) > 3:
        text += f"...и еще {len(matching_items) - 3} позиций\n"
    
    text += "\n"
    
    # Добавляем информацию об отзывах
    if reviews:
        avg_rating = sum(r['rating'] for r in reviews) / len(reviews)
        text += f"⭐ *Рейтинг:* {avg_rating:.1f} ({len(reviews)} отзывов)\n"
    else:
        text += "⭐ *Рейтинг:* Нет отзывов\n"
    
    await message.answer(
        text,
        reply_markup=get_full_place_details_keyboard(
            place_id, page, total_pages, f"menu_search_page:{query}"
        ),
        parse_mode="Markdown"
    )
    
    # Очищаем состояние
    await state.clear()

@router.callback_query(F.data.startswith("menu_search_page:"))
async def callback_menu_search_page(callback: CallbackQuery):
    """Обработчик пагинации для результатов поиска по меню"""
    # Формат: menu_search_page:query:page
    parts = callback.data.split(":")
    query = parts[1]
    page = int(parts[2])
    
    db = Database()
    total = await db.count_search_results(query)
    
    # Получаем запрошенную страницу результатов
    per_page = 1  # Показываем по одному заведению на странице
    total_pages = math.ceil(total / per_page)
    offset = (page - 1) * per_page
    
    places = await db.search_places_by_menu(query, limit=per_page, offset=offset)
    
    if not places:
        await callback.message.edit_text(
            "К сожалению, произошла ошибка при получении данных.",
            reply_markup=get_start_keyboard()
        )
        await callback.answer()
        return
    
    place = places[0]
    place_id = place['id']
    
    # Получаем позиции меню для заведения, соответствующие запросу
    menu_items = await db.get_menu_items_by_place_id(place_id)
    matching_items = [item for item in menu_items if query.lower() in item['name'].lower() or query.lower() in item['category'].lower()]
    
    # Получаем отзывы
    reviews = await db.get_reviews_by_place_id(place_id)
    
    # Формируем полный текст с информацией о заведении
    text = f"🔍 *Результаты поиска по запросу:* {query}\n\n"
    text += f"*{place['name']}*\n"
    text += f"📍 *Адрес:* {place['address']}\n\n"
    
    # Показываем найденные позиции меню
    text += f"*Найденные позиции меню:*\n"
    for item in matching_items[:3]:  # Показываем только первые 3 позиции
        text += f"• {item['name']} - {item['price']} руб. ({item['category']})\n"
    
    if len(matching_items) > 3:
        text += f"...и еще {len(matching_items) - 3} позиций\n"
    
    text += "\n"
    
    # Добавляем информацию об отзывах
    if reviews:
        avg_rating = sum(r['rating'] for r in reviews) / len(reviews)
        text += f"⭐ *Рейтинг:* {avg_rating:.1f} ({len(reviews)} отзывов)\n"
    else:
        text += "⭐ *Рейтинг:* Нет отзывов\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_full_place_details_keyboard(
            place_id, page, total_pages, f"menu_search_page:{query}"
        ),
        parse_mode="Markdown"
    )
    
    await callback.answer() 