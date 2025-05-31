from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from typing import List, Optional, Dict, Any
from datetime import datetime

def get_start_keyboard():
    """Клавиатура для стартового меню"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🍽️ Бизнес-ланчи", callback_data="business_lunch"),
        width=1
    )
    builder.row(
        InlineKeyboardButton(text="🔍 Поиск по меню", callback_data="menu_search"),
        width=1
    )
    builder.row(
        InlineKeyboardButton(text="💨 Кальяны", callback_data="hookah"),
        width=1
    )
    
    return builder.as_markup()

def get_place_details_keyboard(place_id: int, has_route: bool = True):
    """Клавиатура для детальной информации о заведении"""
    builder = InlineKeyboardBuilder()
    
    if has_route:
        builder.row(
            InlineKeyboardButton(
                text="🗺️ Построить маршрут",
                callback_data=f"route:{place_id}"
            ),
            width=1
        )
    
    # Добавляем кнопку для просмотра комментария администратора
    builder.row(
        InlineKeyboardButton(
            text="💬 Комментарий администратора",
            callback_data=f"admin_comment:{place_id}"
        ),
        width=1
    )
    
    # Добавляем кнопку для просмотра всех отзывов
    builder.row(
        InlineKeyboardButton(
            text="📝 Посмотреть все отзывы",
            callback_data=f"all_reviews:{place_id}"
        ),
        width=1
    )
    
    # Добавляем кнопку для просмотра бизнес-ланчей на все дни
    builder.row(
        InlineKeyboardButton(
            text="📆 Бизнес-ланчи на все дни",
            callback_data=f"all_lunches:{place_id}"
        ),
        width=1
    )
    
    builder.row(
        InlineKeyboardButton(
            text="⭐ Оценить заведение",
            callback_data=f"review:{place_id}"
        ),
        width=1
    )
    
    builder.row(
        InlineKeyboardButton(
            text="« Назад",
            callback_data="back_to_list"
        ),
        width=1
    )
    
    return builder.as_markup()

def get_review_keyboard(place_id: int):
    """Клавиатура для оценки заведения"""
    builder = InlineKeyboardBuilder()
    
    for rating in range(1, 6):
        builder.add(
            InlineKeyboardButton(
                text=f"{'⭐' * rating}",
                callback_data=f"rate:{place_id}:{rating}"
            )
        )
    
    builder.adjust(5)
    
    builder.row(
        InlineKeyboardButton(
            text="« Отмена",
            callback_data=f"place:{place_id}"
        ),
        width=1
    )
    
    return builder.as_markup()

def get_pagination_keyboard(
    callback_prefix: str,
    total_pages: int,
    current_page: int,
    additional_button: Optional[InlineKeyboardButton] = None
):
    """Клавиатура для пагинации"""
    builder = InlineKeyboardBuilder()
    
    if current_page > 1:
        builder.add(
            InlineKeyboardButton(
                text="« Пред.",
                callback_data=f"{callback_prefix}:{current_page - 1}"
            )
        )
    
    builder.add(
        InlineKeyboardButton(
            text=f"{current_page}/{total_pages}",
            callback_data="pagination_info"
        )
    )
    
    if current_page < total_pages:
        builder.add(
            InlineKeyboardButton(
                text="След. »",
                callback_data=f"{callback_prefix}:{current_page + 1}"
            )
        )
    
    builder.adjust(3)
    
    if additional_button:
        builder.row(additional_button, width=1)
    
    builder.row(
        InlineKeyboardButton(
            text="« Главное меню",
            callback_data="start"
        ),
        width=1
    )
    
    return builder.as_markup()

def get_search_results_keyboard(places: List[dict], page: int, total_pages: int, callback_prefix: str):
    """Клавиатура для отображения результатов поиска"""
    builder = InlineKeyboardBuilder()
    
    for place in places:
        builder.row(
            InlineKeyboardButton(
                text=place['name'],
                callback_data=f"place:{place['id']}"
            ),
            width=1
        )
    
    # Добавляем пагинацию
    if page > 1:
        builder.add(
            InlineKeyboardButton(
                text="« Пред.",
                callback_data=f"{callback_prefix}:{page - 1}"
            )
        )
    
    builder.add(
        InlineKeyboardButton(
            text=f"{page}/{total_pages}",
            callback_data="pagination_info"
        )
    )
    
    if page < total_pages:
        builder.add(
            InlineKeyboardButton(
                text="След. »",
                callback_data=f"{callback_prefix}:{page + 1}"
            )
        )
    
    builder.adjust(3)
    
    builder.row(
        InlineKeyboardButton(
            text="« Главное меню",
            callback_data="start"
        ),
        width=1
    )
    
    return builder.as_markup()

def get_full_place_details_keyboard(place_id: int, page: int, total_pages: int, callback_prefix: str, weekday: Optional[int] = None):
    """
    Клавиатура для полной информации о заведении с навигацией по списку
    
    Args:
        place_id: ID заведения
        page: Текущая страница
        total_pages: Общее количество страниц
        callback_prefix: Префикс для callback_data
        weekday: День недели (1-7) или None для текущего дня
    """
    builder = InlineKeyboardBuilder()
    
    # Если передан день недели, добавляем его в callback_data
    weekday_param = f":{weekday}" if weekday is not None else ""
    
    # Добавляем кнопку подробнее о заведении
    builder.row(
        InlineKeyboardButton(
            text="📋 Подробнее о заведении",
            callback_data=f"place:{place_id}{weekday_param}"
        ),
        width=1
    )
    
    # Добавляем навигационные кнопки
    nav_buttons = []
    
    if page > 1:
        builder.add(
            InlineKeyboardButton(
                text="« Пред. заведение",
                callback_data=f"{callback_prefix}:{page - 1}{weekday_param}"
            )
        )
    
    if page < total_pages:
        builder.add(
            InlineKeyboardButton(
                text="След. заведение »",
                callback_data=f"{callback_prefix}:{page + 1}{weekday_param}"
            )
        )
    
    builder.adjust(2)
    
    # Добавляем кнопки дней недели, если не передан конкретный день
    if weekday is None:
        # Получаем текущий день недели
        current_weekday = datetime.now().isoweekday()
        builder.row(
            InlineKeyboardButton(
                text="📅 Выбрать день недели",
                callback_data=f"select_day:{place_id}:{page}"
            ),
            width=1
        )
    
    # Кнопка возврата в главное меню
    builder.row(
        InlineKeyboardButton(
            text="« Главное меню",
            callback_data="start"
        ),
        width=1
    )
    
    return builder.as_markup()

def get_weekday_selection_keyboard(place_id: int, page: int, callback_prefix: str):
    """
    Клавиатура для выбора дня недели
    
    Args:
        place_id: ID заведения
        page: Текущая страница для возврата
        callback_prefix: Префикс для callback_data
    """
    builder = InlineKeyboardBuilder()
    
    weekdays = {
        1: "Понедельник", 
        2: "Вторник", 
        3: "Среда", 
        4: "Четверг", 
        5: "Пятница", 
        6: "Суббота", 
        7: "Воскресенье"
    }
    
    # Текущий день недели
    current_weekday = datetime.now().isoweekday()
    
    # Добавляем кнопки для всех дней недели
    for weekday, name in weekdays.items():
        text = name
        if weekday == current_weekday:
            text = f"🔹 {name} (сегодня)"
        
        builder.row(
            InlineKeyboardButton(
                text=text,
                callback_data=f"{callback_prefix}:{page}:{weekday}"
            ),
            width=1
        )
    
    # Кнопка возврата к заведению
    builder.row(
        InlineKeyboardButton(
            text="« Назад к заведению",
            callback_data=f"place:{place_id}"
        ),
        width=1
    )
    
    return builder.as_markup()

def get_all_lunches_keyboard(place_id: int, lunches: List[Dict[str, Any]]):
    """
    Клавиатура для отображения всех бизнес-ланчей заведения по дням недели
    
    Args:
        place_id: ID заведения
        lunches: Список бизнес-ланчей
    """
    builder = InlineKeyboardBuilder()
    
    # Кнопка возврата к заведению
    builder.row(
        InlineKeyboardButton(
            text="« Назад к заведению",
            callback_data=f"place:{place_id}"
        ),
        width=1
    )
    
    return builder.as_markup()

def get_back_to_place_keyboard(place_id: int):
    """Клавиатура для возврата к информации о заведении"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="« Назад к заведению",
            callback_data=f"place:{place_id}"
        ),
        width=1
    )
    
    return builder.as_markup() 