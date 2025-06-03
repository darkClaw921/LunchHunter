from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.database.database import Database
from app.keyboards import get_admin_city_selection_keyboard, get_places_pagination_keyboard
from loguru import logger
import json
import math

router = Router()
db = Database()

# Определяем состояния FSM для добавления заведения
class AddPlaceStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_address = State()
    waiting_for_category = State()
    waiting_for_city = State()
    waiting_for_photo = State()
    waiting_for_admin_comment = State()

# Определяем состояния FSM для добавления бизнес-ланча
class AddLunchStates(StatesGroup):
    waiting_for_place_selection = State()
    waiting_for_json = State()
    waiting_for_place = State()
    waiting_for_price = State()
    waiting_for_start_time = State()
    waiting_for_end_time = State()
    waiting_for_description = State()
    waiting_for_weekday = State()

# Определяем состояния FSM для добавления позиции меню
class AddMenuItemStates(StatesGroup):
    waiting_for_place_selection = State()
    waiting_for_json = State()
    waiting_for_place = State()
    waiting_for_name = State()
    waiting_for_price = State()
    waiting_for_category = State()
    waiting_for_description = State()
    waiting_for_menu_category = State()  # Новое состояние для темы меню

# Команда для добавления нового заведения
@router.message(Command("add_place"))
async def cmd_add_place(message: Message, state: FSMContext):
    """Обработчик команды /add_place для добавления нового заведения"""
    # Проверяем, является ли пользователь администратором
    user_id = message.from_user.id
    is_admin = await db.is_admin(user_id)
    
    if not is_admin:
        await message.answer("У вас нет прав для выполнения этой команды. Только администраторы могут добавлять заведения.")
        return
    
    await message.answer("Добавление нового заведения. Введите название заведения:")
    await state.set_state(AddPlaceStates.waiting_for_name)

# Обработчик названия заведения
@router.message(AddPlaceStates.waiting_for_name)
async def process_place_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите адрес заведения:")
    await state.set_state(AddPlaceStates.waiting_for_address)

# Обработчик адреса заведения
@router.message(AddPlaceStates.waiting_for_address)
async def process_place_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    await message.answer("Введите категорию заведения (например, 'кафе', 'ресторан', 'бар'):")
    await state.set_state(AddPlaceStates.waiting_for_category)

# Обработчик категории заведения
@router.message(AddPlaceStates.waiting_for_category)
async def process_place_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text)
    await message.answer("Выберите город заведения:", 
                        reply_markup=get_admin_city_selection_keyboard())
    await state.set_state(AddPlaceStates.waiting_for_city)

# Обработчик выбора города через инлайн-кнопки
@router.callback_query(F.data.startswith("admin_city:"))
async def process_place_city_callback(callback: CallbackQuery, state: FSMContext):
    city = callback.data.split(":")[1]  # Получаем название города из callback_data
    await state.update_data(city=city)
    
    # Отправляем сообщение о выбранном городе
    await callback.message.edit_text(f"Выбран город: {city}")
    await callback.answer()
    
    # Переходим к следующему шагу
    await callback.message.answer("Отправьте фотографию заведения (или введите 'пропустить', если у вас нет фото):")
    await state.set_state(AddPlaceStates.waiting_for_photo)

# Обработчик ввода города (текстом)
@router.message(AddPlaceStates.waiting_for_city)
async def process_place_city(message: Message, state: FSMContext):
    city = message.text
    if city not in ["Липецк", "Ковров"]:
        await message.answer("Пожалуйста, выберите один из доступных городов из списка кнопок")
        return
    
    await state.update_data(city=city)
    await message.answer("Отправьте фотографию заведения (или введите 'пропустить', если у вас нет фото):")
    await state.set_state(AddPlaceStates.waiting_for_photo)

# Обработчик фотографии заведения
@router.message(AddPlaceStates.waiting_for_photo)
async def process_place_photo(message: Message, state: FSMContext):
    if message.photo:
        # Если отправлена фотография, сохраняем её ID
        photo_id = message.photo[-1].file_id
        await state.update_data(photo_id=photo_id)
    elif message.text.lower() == "пропустить":
        # Если пользователь хочет пропустить фото
        await state.update_data(photo_id=None)
    else:
        await message.answer("Пожалуйста, отправьте фотографию или введите 'пропустить'.")
        return
    
    await message.answer("Введите комментарий администратора (или введите 'пропустить'):")
    await state.set_state(AddPlaceStates.waiting_for_admin_comment)

# Обработчик комментария администратора
@router.message(AddPlaceStates.waiting_for_admin_comment)
async def process_place_comment(message: Message, state: FSMContext):
    admin_comment = None
    if message.text.lower() != "пропустить":
        admin_comment = message.text
    
    # Получаем все данные из состояния
    data = await state.get_data()
    name = data.get("name")
    address = data.get("address")
    category = data.get("category")
    city = data.get("city")
    photo_id = data.get("photo_id")
    
    try:
        # Добавляем заведение в базу данных
        place_id = await db.add_place(
            name=name,
            address=address,
            category=category,
            city=city,
            photo_id=photo_id,
            admin_comment=admin_comment
        )
        
        await message.answer(f"Заведение '{name}' успешно добавлено! ID: {place_id}")
        logger.info(f"Добавлено новое заведение: {name} (ID: {place_id})")
    except Exception as e:
        await message.answer(f"Произошла ошибка при добавлении заведения: {str(e)}")
        logger.error(f"Ошибка при добавлении заведения: {str(e)}")
    
    # Сбрасываем состояние
    await state.clear()

# Команда для добавления нового бизнес-ланча через JSON
@router.message(Command("add_lunch"))
async def cmd_add_lunch_json(message: Message, state: FSMContext):
    """Обработчик команды /add_lunch для добавления бизнес-ланча через JSON формат"""
    # Проверяем, является ли пользователь администратором
    user_id = message.from_user.id
    is_admin = await db.is_admin(user_id)
    
    if not is_admin:
        await message.answer("У вас нет прав для выполнения этой команды. Только администраторы могут добавлять бизнес-ланчи.")
        return
    
    # Проверяем, есть ли у пользователя установленный город
    city = await db.get_user_city(user_id)
    if not city:
        await message.answer("Пожалуйста, сначала выберите город с помощью команды /start.")
        return
    
    # Получаем список заведений для данного города
    places = await db.get_places_for_admin(city)
    
    if not places:
        await message.answer(f"В городе {city} нет добавленных заведений. Сначала добавьте заведение с помощью /add_place.")
        return
    
    # Сохраняем список заведений и информацию для пагинации
    total_places = len(places)
    items_per_page = 5
    total_pages = math.ceil(total_places / items_per_page)
    current_page = 1
    
    await state.update_data(
        places=places,
        current_page=current_page,
        total_pages=total_pages,
        items_per_page=items_per_page
    )
    
    # Отображаем первую страницу заведений
    await message.answer(
        "Выберите заведение для добавления бизнес-ланча:",
        reply_markup=get_places_pagination_keyboard(
            places, current_page, total_pages, "admin_lunch", items_per_page
        )
    )
    
    await state.set_state(AddLunchStates.waiting_for_place_selection)

# Обработчик пагинации для выбора заведения при добавлении бизнес-ланча
@router.callback_query(F.data.startswith("admin_lunch_page:"))
async def process_lunch_place_pagination(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split(":")[1])
    
    data = await state.get_data()
    places = data.get("places", [])
    total_pages = data.get("total_pages", 1)
    items_per_page = data.get("items_per_page", 5)
    
    await state.update_data(current_page=page)
    
    await callback.message.edit_text(
        "Выберите заведение для добавления бизнес-ланча:",
        reply_markup=get_places_pagination_keyboard(
            places, page, total_pages, "admin_lunch", items_per_page
        )
    )
    
    await callback.answer()

# Обработчик выбора заведения для бизнес-ланча
@router.callback_query(F.data.startswith("admin_lunch:"))
async def process_lunch_place_selected(callback: CallbackQuery, state: FSMContext):
    place_id = int(callback.data.split(":")[1])
    
    # Получаем информацию о выбранном заведении
    place = await db.get_place_by_id(place_id)
    if not place:
        await callback.message.edit_text("Ошибка: заведение не найдено.")
        await state.clear()
        return
    
    await state.update_data(place_id=place_id, place_name=place["name"])
    
    # Выводим информацию о формате JSON и запрашиваем его
    json_format = '''{
  "business_lunch": {
    "time": "12:00 до 15:00", // Время бизнес-ланча
    "price": 380, // Цена бизнес-ланча
    "days": {
      "понедельник": {
        "positions": ["Салат 'Мимоза'", "Суп с фрикадельками", "Котлета домашняя / картофель"]
      },
      "вторник": {
        "positions": ["Салат 'Коул Слоу'", "Лапша с цыплёнком", "Шницель куриный / картофель"]
      }
      // и т.д. для других дней
    },
    "additional": "Морс + хлеб" // Дополнительная информация
  }
}'''
    
    await callback.message.edit_text(
        f"Выбрано заведение: {place['name']} ({place['address']})\n\n"
        f"Отправьте информацию о бизнес-ланче в формате JSON.\n"
        f"Пример формата:\n```{json_format}```\n\n"
        f"Или отправьте 'отмена' для отмены."
    )
    
    await state.set_state(AddLunchStates.waiting_for_json)
    await callback.answer()

# Обработчик отмены операции
@router.callback_query(F.data == "cancel_admin")
async def process_admin_cancel(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Операция отменена.")
    await state.clear()
    await callback.answer()

# Обработчик получения JSON для бизнес-ланча
@router.message(AddLunchStates.waiting_for_json)
async def process_lunch_json_input(message: Message, state: FSMContext):
    if message.text.lower() == "отмена":
        await message.answer("Операция отменена.")
        await state.clear()
        return
    
    data = await state.get_data()
    place_id = data.get("place_id")
    place_name = data.get("place_name")
    
    # Словарь для преобразования названий дней недели в числовой формат
    weekday_map = {
        "понедельник": 1,
        "вторник": 2,
        "среда": 3,
        "четверг": 4,
        "пятница": 5,
        "суббота": 6,
        "воскресенье": 7,
        "каждый день": 0
    }
    
    try:
        # Парсим JSON
        data = json.loads(message.text)
        lunch_data = data.get("business_lunch", {})
        
        # Получаем общие данные для всех дней
        price = lunch_data.get("price")
        if not price:
            await message.answer("Ошибка: не указана цена бизнес-ланча (price).")
            return
        
        # Парсим время
        time_str = lunch_data.get("time", "")
        if "до" in time_str:
            try:
                start_time, end_time = time_str.split("до")
                start_time = start_time.strip()
                end_time = end_time.strip()
            except:
                await message.answer("Ошибка: неверный формат времени. Используйте формат 'HH:MM до HH:MM'.")
                return
        else:
            await message.answer("Ошибка: неверный формат времени. Используйте формат 'HH:MM до HH:MM'.")
            return
        
        # Получаем дополнительную информацию
        additional = lunch_data.get("additional", "")
        
        # Обрабатываем информацию по дням недели
        days = lunch_data.get("days", {})
        added_days = []
        
        for day_name, day_data in days.items():
            # Получаем числовой код дня недели
            weekday = weekday_map.get(day_name.lower())
            if weekday is None:
                await message.answer(f"Предупреждение: неизвестный день недели '{day_name}'. Пропускаем.")
                continue
            
            # Формируем описание ланча для этого дня
            positions = day_data.get("positions", [])
            description = "\n".join(positions)
            if additional:
                description += f"\n\n{additional}"
            
            # Добавляем бизнес-ланч в базу данных
            try:
                lunch_id = await db.add_business_lunch(
                    place_id=place_id,
                    price=price,
                    start_time=start_time,
                    end_time=end_time,
                    description=description,
                    weekday=weekday
                )
                added_days.append((weekday, day_name))
                logger.info(f"Добавлен бизнес-ланч для заведения ID:{place_id} на день: {day_name} (ID: {lunch_id})")
            except Exception as e:
                await message.answer(f"Ошибка при добавлении ланча на {day_name}: {str(e)}")
                logger.error(f"Ошибка при добавлении ланча: {str(e)}")
        
        # Формируем итоговое сообщение
        if added_days:
            days_text = ", ".join([f"{day_name}" for _, day_name in added_days])
            await message.answer(
                f"✅ Бизнес-ланч для '{place_name}' успешно добавлен на следующие дни: {days_text}\n"
                f"⏰ Время: {start_time} - {end_time}\n"
                f"💰 Цена: {price} руб."
            )
        else:
            await message.answer("⚠️ Не удалось добавить ни одного бизнес-ланча. Проверьте формат данных.")
        
    except json.JSONDecodeError:
        await message.answer("Ошибка: неверный формат JSON. Пожалуйста, проверьте синтаксис и отправьте снова.")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")
        logger.error(f"Ошибка при обработке JSON для бизнес-ланча: {str(e)}")
    
    # Сбрасываем состояние
    await state.clear()

# Команда для добавления новой позиции меню
@router.message(Command("add_menu"))
async def cmd_add_menu_item(message: Message, state: FSMContext):
    """Обработчик команды /add_menu для добавления позиции меню"""
    # Проверяем, является ли пользователь администратором
    user_id = message.from_user.id
    is_admin = await db.is_admin(user_id)
    
    if not is_admin:
        await message.answer("У вас нет прав для выполнения этой команды. Только администраторы могут добавлять позиции меню.")
        return
    
    # Проверяем, есть ли у пользователя установленный город
    city = await db.get_user_city(user_id)
    if not city:
        await message.answer("Пожалуйста, сначала выберите город с помощью команды /start.")
        return
    
    # Получаем список заведений для данного города
    places = await db.get_places_for_admin(city)
    
    if not places:
        await message.answer(f"В городе {city} нет добавленных заведений. Сначала добавьте заведение.")
        return
    
    # Сохраняем список заведений и информацию для пагинации
    total_places = len(places)
    items_per_page = 5
    total_pages = math.ceil(total_places / items_per_page)
    current_page = 1
    
    await state.update_data(
        places=places,
        current_page=current_page,
        total_pages=total_pages,
        items_per_page=items_per_page
    )
    
    # Отображаем первую страницу заведений
    await message.answer(
        "Выберите заведение для добавления позиции меню:",
        reply_markup=get_places_pagination_keyboard(
            places, current_page, total_pages, "admin_menu", items_per_page
        )
    )
    
    await state.set_state(AddMenuItemStates.waiting_for_place_selection)

# Обработчик пагинации для выбора заведения при добавлении позиции меню
@router.callback_query(F.data.startswith("admin_menu_page:"))
async def process_menu_place_pagination(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split(":")[1])
    
    data = await state.get_data()
    places = data.get("places", [])
    total_pages = data.get("total_pages", 1)
    items_per_page = data.get("items_per_page", 5)
    
    await state.update_data(current_page=page)
    
    await callback.message.edit_text(
        "Выберите заведение для добавления позиции меню:",
        reply_markup=get_places_pagination_keyboard(
            places, page, total_pages, "admin_menu", items_per_page
        )
    )
    
    await callback.answer()

# Обработчик выбора заведения для позиции меню
@router.callback_query(F.data.startswith("admin_menu:"))
async def process_menu_place_selected(callback: CallbackQuery, state: FSMContext):
    place_id = int(callback.data.split(":")[1])
    
    # Получаем информацию о выбранном заведении
    place = await db.get_place_by_id(place_id)
    if not place:
        await callback.message.edit_text("Ошибка: заведение не найдено.")
        await state.clear()
        return
    
    await state.update_data(place_id=place_id, place_name=place["name"])
    
    # Запрашиваем категорию/тему позиций меню
    await callback.message.edit_text(
        f"Выбрано заведение: {place['name']} ({place['address']})\n\n"
        f"Введите общую категорию для добавляемых позиций меню (например, 'напитки', 'десерты', 'кальяны'):"
    )
    
    await state.set_state(AddMenuItemStates.waiting_for_menu_category)
    await callback.answer()

# Новый обработчик для получения категории позиций меню
@router.message(AddMenuItemStates.waiting_for_menu_category)
async def process_menu_category_input(message: Message, state: FSMContext):
    category = message.text.strip()
    
    if not category or category.lower() == "отмена":
        await message.answer("Операция отменена.")
        await state.clear()
        return
    
    # Сохраняем категорию в состоянии
    await state.update_data(menu_category=category)
    
    # Получаем данные о заведении
    data = await state.get_data()
    place_name = data.get("place_name")
    
    # Выводим информацию о формате JSON и запрашиваем его
    json_format = '''{
  "menu_items": [
    {
      "name": "SPATEN",
      "description": "светлый фильтр. лагер",
      "volume": "500 мл",
      "price": 290
    },
    {
      "name": "SPATEN",
      "description": "светлый фильтр. лагер",
      "volume": "300 мл",
      "price": 190
    },
    {
      "name": "HOEGAARDEN",
      "description": "нефильтр. лагер",
      "volume": "500 мл",
      "price": 290
    }
  ]
}'''
    
    await message.answer(
        f"Выбрана категория: {category}\n\n"
        f"Отправьте информацию о позициях меню в формате JSON.\n"
        f"Пример формата:\n```{json_format}```\n\n"
        f"Или отправьте 'отмена' для отмены."
    )
    
    await state.set_state(AddMenuItemStates.waiting_for_json)

# Обработчик получения JSON для позиций меню
@router.message(AddMenuItemStates.waiting_for_json)
async def process_menu_json_input(message: Message, state: FSMContext):
    if message.text.lower() == "отмена":
        await message.answer("Операция отменена.")
        await state.clear()
        return
    
    data = await state.get_data()
    place_id = data.get("place_id")
    place_name = data.get("place_name")
    menu_category = data.get("menu_category", "напиток")  # Используем полученную категорию
    
    try:
        # Парсим JSON
        data = json.loads(message.text)
        menu_items = data.get("menu_items", [])
        
        if not menu_items:
            await message.answer("Ошибка: не найдены позиции меню в JSON.")
            return
        
        added_items = []
        
        for item in menu_items:
            name = item.get("name")
            description = item.get("description", "")
            price = item.get("price")
            volume = item.get("volume", "")
            
            # Добавляем объем в описание, если он указан
            if volume:
                if description:
                    description = f"{description}, {volume}"
                else:
                    description = volume
            
            # Используем категорию, указанную пользователем
            category = menu_category
            
            # Проверяем обязательные поля
            if not name:
                continue
            if not price:
                continue
            
            try:
                # Добавляем позицию меню в базу данных
                menu_id = await db.add_menu_item(
                    place_id=place_id,
                    name=name,
                    price=price,
                    category=category,
                    description=description
                )
                
                added_items.append((name, price))
                logger.info(f"Добавлена позиция меню '{name}' для заведения '{place_name}' (ID: {menu_id})")
            except Exception as e:
                await message.answer(f"Ошибка при добавлении позиции '{name}': {str(e)}")
                logger.error(f"Ошибка при добавлении позиции меню: {str(e)}")
        
        # Формируем итоговое сообщение
        if added_items:
            items_text = "\n".join([f"- {name} ({price} руб.)" for name, price in added_items])
            await message.answer(
                f"✅ Добавлены следующие позиции меню категории '{menu_category}' для '{place_name}':\n\n{items_text}\n\n"
                f"Всего добавлено позиций: {len(added_items)}"
            )
        else:
            await message.answer("⚠️ Не удалось добавить ни одной позиции меню. Проверьте формат данных.")
        
    except json.JSONDecodeError:
        await message.answer("Ошибка: неверный формат JSON. Пожалуйста, проверьте синтаксис и отправьте снова.")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")
        logger.error(f"Ошибка при обработке JSON для позиций меню: {str(e)}")
    
    # Сбрасываем состояние
    await state.clear()

# Команда для установки статуса администратора (только для технических целей)
@router.message(Command("make_admin"))
async def cmd_make_admin(message: Message):
    """Техническая команда для назначения администратора (только для владельцев бота)"""
    # Проверяем, что команду вызвал владелец бота
    if message.from_user.id != 400923372:
        return
    if len(message.text.split()) != 2:
        return  # Скрытая команда, не отвечаем на некорректный вызов
    
    try:
        user_id = int(message.text.split()[1])
        result = await db.set_admin_status(user_id, True)
        if result:
            logger.info(f"Пользователь {user_id} назначен администратором")
            await message.answer(f"Пользователь {user_id} назначен администратором")
        else:
            logger.warning(f"Не удалось назначить пользователя {user_id} администратором (пользователь не найден)")
            await message.answer(f"Пользователь {user_id} не найден")
    except Exception as e:
        logger.error(f"Ошибка при назначении администратора: {str(e)}") 