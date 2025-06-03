from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from app.database import Database
from app.keyboards import (
    get_search_results_keyboard, 
    get_start_keyboard, 
    get_full_place_details_keyboard,
    get_menu_search_pagination_keyboard,
    get_menu_categories_keyboard,
    get_menu_items_by_category_keyboard,
    get_back_to_place_keyboard
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
    
    # Получаем город пользователя
    user_id = message.from_user.id
    db = Database()
    city = await db.get_user_city(user_id)
    
    if not city:
        await message.answer(
            "Пожалуйста, сначала выберите город с помощью команды /start.",
            reply_markup=get_start_keyboard()
        )
        await state.clear()
        return
    
    # Выполняем поиск
    total = await db.count_search_results(query, city)
    
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
    
    places = await db.search_places_by_menu(query, city, limit=per_page, offset=offset)
    
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
        reply_markup=get_menu_search_pagination_keyboard(
            places, page, total_pages, query, place_id
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
    
    # Получаем город пользователя
    user_id = callback.from_user.id
    db = Database()
    city = await db.get_user_city(user_id)
    
    if not city:
        await callback.message.edit_text(
            "Пожалуйста, сначала выберите город с помощью команды /start.",
            reply_markup=get_start_keyboard()
        )
        await callback.answer()
        return
    
    total = await db.count_search_results(query, city)
    
    # Получаем запрошенную страницу результатов
    per_page = 1  # Показываем по одному заведению на странице
    total_pages = math.ceil(total / per_page)
    offset = (page - 1) * per_page
    
    places = await db.search_places_by_menu(query, city, limit=per_page, offset=offset)
    
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
        reply_markup=get_menu_search_pagination_keyboard(
            places, page, total_pages, query, place_id
        ),
        parse_mode="Markdown"
    )
    
    await callback.answer()

@router.callback_query(F.data.startswith("menu_all_items:"))
async def callback_menu_all_items(callback: CallbackQuery):
    """Обработчик для просмотра всех позиций меню по запросу"""
    # Формат: menu_all_items:place_id:query
    parts = callback.data.split(":")
    place_id = int(parts[1])
    query = parts[2]
    
    db = Database()
    
    # Получаем информацию о заведении
    place = await db.get_place_by_id(place_id)
    if not place:
        await callback.answer("Заведение не найдено", show_alert=True)
        return
    
    # Получаем все позиции меню для заведения
    menu_items = await db.get_menu_items_by_place_id(place_id)
    matching_items = [item for item in menu_items if query.lower() in item['name'].lower() or query.lower() in item['category'].lower()]
    
    if not matching_items:
        await callback.answer("Позиции меню не найдены", show_alert=True)
        return
    
    # Формируем текст с информацией о позициях меню
    text = f"📋 *Все позиции меню по запросу '{query}' в {place['name']}:*\n\n"
    
    # Группируем позиции по категориям
    categories = {}
    for item in matching_items:
        category = item['category']
        if category not in categories:
            categories[category] = []
        categories[category].append(item)
    
    # Выводим позиции по категориям
    for category, items in categories.items():
        text += f"*{category}:*\n"
        for item in items:
            desc = f"🗒 {item['description']}" if item['description'] else ""
            text += f"• *{item['name']}* \n💵{item['price']} руб.\n{desc}\n"
        text += "\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_back_to_place_keyboard(place_id),
        parse_mode="Markdown"
    )
    
    await callback.answer()

@router.callback_query(F.data.startswith("menu_categories:"))
async def callback_menu_categories(callback: CallbackQuery):
    """Обработчик для просмотра всех категорий меню заведения"""
    # Формат: menu_categories:place_id
    parts = callback.data.split(":")
    place_id = int(parts[1])
    
    db = Database()
    
    # Получаем информацию о заведении
    place = await db.get_place_by_id(place_id)
    if not place:
        await callback.answer("Заведение не найдено", show_alert=True)
        return
    
    # Получаем все категории меню
    categories = await db.get_menu_categories_by_place_id(place_id)
    
    if not categories:
        await callback.answer("Категории меню не найдены", show_alert=True)
        return
    
    # Формируем текст с информацией о категориях меню
    text = f"🔍 *Категории меню в {place['name']}:*\n\n"
    text += "Выберите категорию для просмотра позиций меню:"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_menu_categories_keyboard(place_id, categories),
        parse_mode="Markdown"
    )
    
    await callback.answer()

@router.callback_query(F.data.startswith("menu_category:"))
async def callback_menu_category(callback: CallbackQuery):
    """Обработчик для просмотра позиций меню по категории"""
    # Формат: menu_category:place_id:category
    parts = callback.data.split(":")
    place_id = int(parts[1])
    category = parts[2]
    
    db = Database()
    
    # Получаем информацию о заведении
    place = await db.get_place_by_id(place_id)
    if not place:
        await callback.answer("Заведение не найдено", show_alert=True)
        return
    
    # Получаем позиции меню по категории
    menu_items = await db.get_menu_items_by_category(place_id, category)
    
    if not menu_items:
        await callback.answer("Позиции меню не найдены", show_alert=True)
        return
    
    # Формируем текст с информацией о позициях меню
    text = f"📋 *{category} в {place['name']}:*\n\n"
    
    for item in menu_items:
        desc = f"🗒 {item['description']}" if item['description'] else ""
        text += f"• *{item['name']}* \n💵{item['price']} руб.\n{desc}\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_menu_items_by_category_keyboard(place_id, category),
        parse_mode="Markdown"
    )
    
    await callback.answer() 