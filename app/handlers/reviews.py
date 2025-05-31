from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from app.database import Database
from app.keyboards import get_review_keyboard, get_back_to_place_keyboard

router = Router()

class ReviewState(StatesGroup):
    waiting_for_comment = State()

@router.callback_query(F.data.startswith("review:"))
async def callback_review(callback: CallbackQuery):
    """Обработчик кнопки 'Оценить заведение'"""
    place_id = int(callback.data.split(":")[1])
    db = Database()
    
    # Получаем информацию о заведении
    place = await db.get_place_by_id(place_id)
    if not place:
        await callback.answer("Заведение не найдено", show_alert=True)
        return
    
    text = (
        f"⭐ *Оцените заведение: {place['name']}*\n\n"
        "Выберите оценку от 1 до 5 звезд:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_review_keyboard(place_id),
        parse_mode="Markdown"
    )
    
    await callback.answer()

@router.callback_query(F.data.startswith("rate:"))
async def callback_rate(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора оценки"""
    parts = callback.data.split(":")
    place_id = int(parts[1])
    rating = int(parts[2])
    
    # Сохраняем данные в состоянии
    await state.update_data(place_id=place_id, rating=rating)
    await state.set_state(ReviewState.waiting_for_comment)
    
    db = Database()
    place = await db.get_place_by_id(place_id)
    
    text = (
        f"⭐ *Вы поставили оценку {rating} из 5 для {place['name']}*\n\n"
        "Если хотите, оставьте комментарий к вашей оценке.\n"
        "Или нажмите кнопку ниже, чтобы сохранить отзыв без комментария."
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_back_to_place_keyboard(place_id),
        parse_mode="Markdown"
    )
    
    await callback.answer()

@router.message(StateFilter(ReviewState.waiting_for_comment))
async def process_review_comment(message, state: FSMContext):
    """Обработчик ввода комментария к отзыву"""
    comment = message.text.strip()
    
    # Получаем сохраненные данные
    data = await state.get_data()
    place_id = data.get("place_id")
    rating = data.get("rating")
    
    db = Database()
    
    # Сохраняем отзыв в базе данных
    await db.add_review(
        user_id=message.from_user.id,
        place_id=place_id,
        rating=rating,
        comment=comment
    )
    
    place = await db.get_place_by_id(place_id)
    
    text = (
        f"✅ *Спасибо за ваш отзыв о {place['name']}!*\n\n"
        f"Вы поставили оценку: {'⭐' * rating}"
    )
    
    if comment:
        text += f"\n\nВаш комментарий: {comment}"
    
    await message.answer(
        text,
        reply_markup=get_back_to_place_keyboard(place_id),
        parse_mode="Markdown"
    )
    
    # Очищаем состояние
    await state.clear()

@router.callback_query(StateFilter(ReviewState.waiting_for_comment), F.data.startswith("place:"))
async def save_review_without_comment(callback: CallbackQuery, state: FSMContext):
    """Сохранение отзыва без комментария"""
    # Получаем сохраненные данные
    data = await state.get_data()
    place_id = data.get("place_id")
    rating = data.get("rating")
    
    db = Database()
    
    # Сохраняем отзыв в базе данных без комментария
    await db.add_review(
        user_id=callback.from_user.id,
        place_id=place_id,
        rating=rating
    )
    
    # Получаем информацию о заведении
    place = await db.get_place_by_id(place_id)
    
    # Получаем информацию о бизнес-ланче
    business_lunch = await db.get_business_lunch_by_place_id(place_id)
    
    # Получаем отзывы
    reviews = await db.get_reviews_by_place_id(place_id)
    
    # Формируем текст с информацией о заведении (как в callback_place_details)
    text = f"*{place['name']}*\n"
    text += f"📍 *Адрес:* {place['address']}\n\n"
    
    if business_lunch:
        text += f"🍽️ *Бизнес-ланч:*\n"
        text += f"💰 Цена: {business_lunch['price']} руб.\n"
        text += f"⏰ Время: {business_lunch['start_time']} - {business_lunch['end_time']}\n"
        
        if business_lunch['description']:
            text += f"📝 {business_lunch['description']}\n"
        
        text += "\n"
    
    if place['admin_comment']:
        text += f"ℹ️ *Комментарий администратора:*\n{place['admin_comment']}\n\n"
    
    # Добавляем информацию об отзывах
    if reviews:
        avg_rating = sum(r['rating'] for r in reviews) / len(reviews)
        text += f"⭐ *Рейтинг:* {avg_rating:.1f} ({len(reviews)} отзывов)\n\n"
    else:
        text += "⭐ *Рейтинг:* Нет отзывов\n\n"
    
    await callback.answer("Спасибо за ваш отзыв!", show_alert=True)
    
    from app.keyboards import get_place_details_keyboard
    
    await callback.message.edit_text(
        text,
        reply_markup=get_place_details_keyboard(place_id),
        parse_mode="Markdown"
    )
    
    # Очищаем состояние
    await state.clear() 