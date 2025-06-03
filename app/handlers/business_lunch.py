from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.database import Database
from app.keyboards import (
    get_search_results_keyboard, 
    get_place_details_keyboard, 
    get_full_place_details_keyboard,
    get_back_to_place_keyboard,
    get_start_keyboard,
    get_weekday_selection_keyboard,
    get_all_lunches_keyboard
)
from app.utils import get_yandex_maps_url
from datetime import datetime
import math

router = Router()

@router.callback_query(F.data == "business_lunch")
async def callback_business_lunch(callback: CallbackQuery):
    """Обработчик кнопки 'Бизнес-ланчи'"""
    db = Database()
    
    # Получаем город пользователя
    user_id = callback.from_user.id
    city = await db.get_user_city(user_id)
    
    if not city:
        await callback.message.edit_text(
            "Пожалуйста, сначала выберите город, используя команду /start.",
            reply_markup=get_start_keyboard()
        )
        await callback.answer()
        return
    
    # Получаем текущий день недели
    current_weekday = datetime.now().isoweekday()  # 1-7 (пн-вс)
    
    # Получаем количество заведений с бизнес-ланчами на текущий день
    total = await db.count_business_lunches(city, weekday=current_weekday)
    
    if total == 0:
        await callback.message.edit_text(
            f"К сожалению, заведений с бизнес-ланчами в городе {city} на {_get_weekday_name(current_weekday)} пока нет в базе.",
            reply_markup=get_start_keyboard()
        )
        await callback.answer()
        return
    
    # Получаем первую страницу результатов
    page = 1
    per_page = 1  # Показываем по одному заведению на странице
    total_pages = math.ceil(total / per_page)
    offset = (page - 1) * per_page
    
    places = await db.get_business_lunches(city, limit=per_page, offset=offset, weekday=current_weekday)
    
    if not places:
        await callback.message.edit_text(
            "К сожалению, произошла ошибка при получении данных.",
            reply_markup=get_start_keyboard()
        )
        await callback.answer()
        return
    
    place = places[0]
    place_id = place['id']
    
    # Получаем отзывы
    reviews = await db.get_reviews_by_place_id(place_id)
    
    # Формируем полный текст с информацией о заведении
    text = f"🍽️ *Бизнес-ланч на {_get_weekday_name(current_weekday)}*\n\n"
    text += f"*{place['name']}*\n"
    text += f"📍 *Адрес:* {place['address']}\n"
    text += f"🏙️ *Город:* {place['city']}\n\n"
    text += f"🍽️ *Бизнес-ланч:*\n"
    text += f"💰 Цена: {place['price']} руб.\n"
    text += f"⏰ Время: {place['start_time']} - {place['end_time']}\n"
    
    if place['description']:
        text += f"📝 {place['description']}\n\n"
    
    # Добавляем информацию об отзывах
    if reviews:
        avg_rating = sum(r['rating'] for r in reviews) / len(reviews)
        text += f"⭐ *Рейтинг:* {avg_rating:.1f} ({len(reviews)} отзывов)\n"
    else:
        text += "⭐ *Рейтинг:* Нет отзывов\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_full_place_details_keyboard(
            place_id, page, total_pages, "business_lunch_page"
        ),
        parse_mode="Markdown"
    )
    
    await callback.answer()

@router.callback_query(F.data.startswith("business_lunch_page:"))
async def callback_business_lunch_page(callback: CallbackQuery):
    """Обработчик пагинации для бизнес-ланчей"""
    parts = callback.data.split(":")
    page = int(parts[1])
    
    # Если указан день недели, используем его, иначе берем текущий
    weekday = int(parts[2]) if len(parts) > 2 else None
    if weekday is None:
        weekday = datetime.now().isoweekday()
    
    db = Database()
    
    # Получаем город пользователя
    user_id = callback.from_user.id
    city = await db.get_user_city(user_id)
    
    if not city:
        await callback.message.edit_text(
            "Пожалуйста, сначала выберите город, используя команду /start.",
            reply_markup=get_start_keyboard()
        )
        await callback.answer()
        return
    
    # Получаем количество заведений с бизнес-ланчами
    total = await db.count_business_lunches(city, weekday=weekday)
    
    # Получаем запрошенную страницу результатов
    per_page = 1  # Показываем по одному заведению на странице
    total_pages = math.ceil(total / per_page)
    offset = (page - 1) * per_page
    
    places = await db.get_business_lunches(city, limit=per_page, offset=offset, weekday=weekday)
    
    if not places:
        await callback.message.edit_text(
            "К сожалению, произошла ошибка при получении данных.",
            reply_markup=get_start_keyboard()
        )
        await callback.answer()
        return
    
    place = places[0]
    place_id = place['id']
    
    # Получаем отзывы
    reviews = await db.get_reviews_by_place_id(place_id)
    
    # Формируем полный текст с информацией о заведении
    text = f"🍽️ *Бизнес-ланч на {_get_weekday_name(weekday)}*\n\n"
    text += f"*{place['name']}*\n"
    text += f"📍 *Адрес:* {place['address']}\n"
    text += f"🏙️ *Город:* {place['city']}\n\n"
    text += f"🍽️ *Бизнес-ланч:*\n"
    text += f"💰 Цена: {place['price']} руб.\n"
    text += f"⏰ Время: {place['start_time']} - {place['end_time']}\n"
    
    if place['description']:
        text += f"📝 {place['description']}\n\n"
    
    # Добавляем информацию об отзывах
    if reviews:
        avg_rating = sum(r['rating'] for r in reviews) / len(reviews)
        text += f"⭐ *Рейтинг:* {avg_rating:.1f} ({len(reviews)} отзывов)\n"
    else:
        text += "⭐ *Рейтинг:* Нет отзывов\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_full_place_details_keyboard(
            place_id, page, total_pages, "business_lunch_page", weekday
        ),
        parse_mode="Markdown"
    )
    
    await callback.answer()

@router.callback_query(F.data.startswith("select_day:"))
async def callback_select_day(callback: CallbackQuery):
    """Обработчик выбора дня недели"""
    parts = callback.data.split(":")
    place_id = int(parts[1])
    page = int(parts[2])
    
    await callback.message.edit_text(
        "📅 *Выберите день недели:*",
        reply_markup=get_weekday_selection_keyboard(
            place_id, page, "business_lunch_day"
        ),
        parse_mode="Markdown"
    )
    
    await callback.answer()

@router.callback_query(F.data.startswith("business_lunch_day:"))
async def callback_business_lunch_day(callback: CallbackQuery):
    """Обработчик выбора конкретного дня недели"""
    parts = callback.data.split(":")
    page = int(parts[1])
    weekday = int(parts[2])
    
    await callback_business_lunch_page(callback)

@router.callback_query(F.data.startswith("place:"))
async def callback_place_details(callback: CallbackQuery):
    """Обработчик для просмотра детальной информации о заведении"""
    parts = callback.data.split(":")
    place_id = int(parts[1])
    
    # Если указан день недели, используем его, иначе берем текущий
    weekday = int(parts[2]) if len(parts) > 2 else None
    
    db = Database()
    
    # Получаем информацию о заведении
    place = await db.get_place_by_id(place_id)
    if not place:
        await callback.answer("Заведение не найдено", show_alert=True)
        return
    
    # Получаем информацию о бизнес-ланче на указанный день
    business_lunch = await db.get_business_lunch_by_place_id(place_id, weekday)
    
    # Получаем отзывы
    reviews = await db.get_reviews_by_place_id(place_id)
    
    # Формируем текст с информацией о заведении
    text = f"*{place['name']}*\n"
    text += f"📍 *Адрес:* {place['address']}\n\n"
    
    if business_lunch:
        if weekday:
            text += f"🍽️ *Бизнес-ланч ({business_lunch['weekday_name']}):*\n"
        else:
            text += f"🍽️ *Бизнес-ланч (сегодня):*\n"
            
        text += f"💰 Цена: {business_lunch['price']} руб.\n"
        text += f"⏰ Время: {business_lunch['start_time']} - {business_lunch['end_time']}\n"
        
        if business_lunch['description']:
            text += f"📝 {business_lunch['description']}\n"
        
        text += "\n"
    
    # Добавляем информацию об отзывах
    if reviews:
        avg_rating = sum(r['rating'] for r in reviews) / len(reviews)
        text += f"⭐ *Рейтинг:* {avg_rating:.1f} ({len(reviews)} отзывов)\n\n"
    else:
        text += "⭐ *Рейтинг:* Нет отзывов\n\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_place_details_keyboard(place_id),
        parse_mode="Markdown"
    )
    
    await callback.answer()

@router.callback_query(F.data == "back_to_list")
async def callback_back_to_list(callback: CallbackQuery):
    """Обработчик кнопки 'Назад'"""
    await callback_business_lunch(callback)

@router.callback_query(F.data.startswith("route:"))
async def callback_route(callback: CallbackQuery):
    """Обработчик кнопки 'Построить маршрут'"""
    place_id = int(callback.data.split(":")[1])
    db = Database()
    
    # Получаем информацию о заведении
    place = await db.get_place_by_id(place_id)
    if not place:
        await callback.answer("Заведение не найдено", show_alert=True)
        return
    
    # Формируем ссылку на Яндекс.Карты
    maps_url = get_yandex_maps_url(place['address'], place['name'])
    
    text = f"*{place['name']}*\n\n"
    text += f"Для построения маршрута перейдите по ссылке:\n{maps_url}"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_place_details_keyboard(place_id, has_route=False),
        parse_mode="Markdown"
    )
    
    await callback.answer()

@router.callback_query(F.data.startswith("admin_comment:"))
async def callback_admin_comment(callback: CallbackQuery):
    """Обработчик кнопки 'Комментарий администратора'"""
    place_id = int(callback.data.split(":")[1])
    db = Database()
    
    # Получаем информацию о заведении
    place = await db.get_place_by_id(place_id)
    if not place:
        await callback.answer("Заведение не найдено", show_alert=True)
        return
    
    if not place['admin_comment']:
        await callback.answer("Комментарий администратора отсутствует", show_alert=True)
        return
    
    text = f"*{place['name']}*\n\n"
    text += f"💬 *Комментарий администратора:*\n{place['admin_comment']}"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_back_to_place_keyboard(place_id),
        parse_mode="Markdown"
    )
    
    await callback.answer()

@router.callback_query(F.data.startswith("all_reviews:"))
async def callback_all_reviews(callback: CallbackQuery):
    """Обработчик кнопки 'Посмотреть все отзывы'"""
    place_id = int(callback.data.split(":")[1])
    db = Database()
    
    # Получаем информацию о заведении
    place = await db.get_place_by_id(place_id)
    if not place:
        await callback.answer("Заведение не найдено", show_alert=True)
        return
    
    # Получаем отзывы
    reviews = await db.get_reviews_by_place_id(place_id)
    
    if not reviews:
        await callback.answer("Отзывы отсутствуют", show_alert=True)
        return
    
    text = f"*{place['name']}* - Отзывы\n\n"
    
    # Рассчитываем средний рейтинг
    avg_rating = sum(r['rating'] for r in reviews) / len(reviews)
    text += f"⭐ *Средний рейтинг:* {avg_rating:.1f} ({len(reviews)} отзывов)\n\n"
    
    # Выводим последние 5 отзывов (или меньше, если их всего меньше 5)
    for i, review in enumerate(reviews[:5], 1):
        text += f"*Отзыв #{i}*\n"
        text += f"⭐ Оценка: {'⭐' * review['rating']}\n"
        if review['comment']:
            text += f"💬 {review['comment']}\n"
        text += "\n"
    
    if len(reviews) > 5:
        text += f"*...и еще {len(reviews) - 5} отзывов*\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_back_to_place_keyboard(place_id),
        parse_mode="Markdown"
    )
    
    await callback.answer()

@router.callback_query(F.data.startswith("all_lunches:"))
async def callback_all_lunches(callback: CallbackQuery):
    """Обработчик кнопки 'Бизнес-ланчи на все дни'"""
    place_id = int(callback.data.split(":")[1])
    db = Database()
    
    # Получаем информацию о заведении
    place = await db.get_place_by_id(place_id)
    if not place:
        await callback.answer("Заведение не найдено", show_alert=True)
        return
    
    # Получаем все бизнес-ланчи для заведения
    lunches = await db.get_business_lunches_for_all_days(place_id)
    
    if not lunches:
        await callback.answer("Информация о бизнес-ланчах отсутствует", show_alert=True)
        return
    
    text = f"*{place['name']}* - Бизнес-ланчи\n\n"
    
    # Сортируем ланчи: сначала "каждый день", потом по дням недели
    lunches.sort(key=lambda x: x['weekday'])
    
    # Выводим информацию о бизнес-ланчах по дням недели
    for lunch in lunches:
        text += f"*{lunch['weekday_name']}*\n"
        text += f"💰 Цена: {lunch['price']} руб.\n"
        text += f"⏰ Время: {lunch['start_time']} - {lunch['end_time']}\n"
        
        if lunch['description']:
            text += f"📝 {lunch['description']}\n"
        
        text += "\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_back_to_place_keyboard(place_id),
        parse_mode="Markdown"
    )
    
    await callback.answer()

def _get_weekday_name(weekday: int) -> str:
    """Возвращает название дня недели по его номеру"""
    weekdays = {
        0: "Каждый день",
        1: "Понедельник",
        2: "Вторник",
        3: "Среда", 
        4: "Четверг",
        5: "Пятница",
        6: "Суббота",
        7: "Воскресенье"
    }
    return weekdays.get(weekday, "Неизвестный день") 