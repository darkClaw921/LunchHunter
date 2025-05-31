from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.database import Database
from app.keyboards import (
    get_search_results_keyboard, 
    get_start_keyboard, 
    get_full_place_details_keyboard
)
import math

router = Router()

@router.callback_query(F.data == "hookah")
async def callback_hookah(callback: CallbackQuery):
    """Обработчик кнопки 'Кальяны'"""
    db = Database()
    
    # Для кальянов используем ту же логику, что и для бизнес-ланчей,
    # но ищем заведения с категорией "кальян"
    query = "кальян"
    total = await db.count_search_results(query)
    
    if total == 0:
        await callback.message.edit_text(
            "К сожалению, заведений с кальянами пока нет в базе.",
            reply_markup=get_start_keyboard()
        )
        await callback.answer()
        return
    
    # Получаем первую страницу результатов
    page = 1
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
    
    # Получаем позиции меню для заведения, связанные с кальянами
    menu_items = await db.get_menu_items_by_place_id(place_id)
    hookah_items = [item for item in menu_items if "кальян" in item['category'].lower()]
    
    # Получаем отзывы
    reviews = await db.get_reviews_by_place_id(place_id)
    
    # Формируем полный текст с информацией о заведении
    text = f"💨 *Заведения с кальянами*\n\n"
    text += f"*{place['name']}*\n"
    text += f"📍 *Адрес:* {place['address']}\n\n"
    
    # Показываем кальяны в меню
    text += f"*Кальяны в меню:*\n"
    for item in hookah_items[:3]:  # Показываем только первые 3 позиции
        text += f"• {item['name']} - {item['price']} руб.\n"
    
    if len(hookah_items) > 3:
        text += f"...и еще {len(hookah_items) - 3} видов кальянов\n"
    
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
            place_id, page, total_pages, f"hookah_page:{query}"
        ),
        parse_mode="Markdown"
    )
    
    await callback.answer()

@router.callback_query(F.data.startswith("hookah_page:"))
async def callback_hookah_page(callback: CallbackQuery):
    """Обработчик пагинации для кальянов"""
    # Формат: hookah_page:query:page
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
    
    # Получаем позиции меню для заведения, связанные с кальянами
    menu_items = await db.get_menu_items_by_place_id(place_id)
    hookah_items = [item for item in menu_items if "кальян" in item['category'].lower()]
    
    # Получаем отзывы
    reviews = await db.get_reviews_by_place_id(place_id)
    
    # Формируем полный текст с информацией о заведении
    text = f"💨 *Заведения с кальянами*\n\n"
    text += f"*{place['name']}*\n"
    text += f"📍 *Адрес:* {place['address']}\n\n"
    
    # Показываем кальяны в меню
    text += f"*Кальяны в меню:*\n"
    for item in hookah_items[:3]:  # Показываем только первые 3 позиции
        text += f"• {item['name']} - {item['price']} руб.\n"
    
    if len(hookah_items) > 3:
        text += f"...и еще {len(hookah_items) - 3} видов кальянов\n"
    
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
            place_id, page, total_pages, f"hookah_page:{query}"
        ),
        parse_mode="Markdown"
    )
    
    await callback.answer() 