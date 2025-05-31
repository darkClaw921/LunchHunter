import asyncio
import os
from app.database import Database
from dotenv import load_dotenv

load_dotenv()

async def seed_database():
    """Заполняет базу данных тестовыми данными"""
    db = Database(os.getenv("DATABASE_NAME", "lunch_hunter.db"))
    await db.create_tables()
    
    # Добавляем тестовые заведения
    print("Добавление тестовых заведений...")
    
    # 1. Ресторан с бизнес-ланчем (разные ланчи по дням недели)
    place1_id = await db.add_place(
        name="Ресторан 'Вкусно и точка'",
        address="ул. Примерная, 10",
        category="ресторан",
        admin_comment="Уютное место с отличным обслуживанием, бизнес-ланчи каждый день разные"
    )
    
    # Понедельник
    await db.add_business_lunch(
        place_id=place1_id,
        price=450.0,
        start_time="12:00",
        end_time="16:00",
        description="Борщ, куриная котлета с пюре, компот",
        weekday=1  # Понедельник
    )
    
    # Вторник
    await db.add_business_lunch(
        place_id=place1_id,
        price=450.0,
        start_time="12:00",
        end_time="16:00",
        description="Куриный суп, рыба с рисом, морс",
        weekday=2  # Вторник
    )
    
    # Среда
    await db.add_business_lunch(
        place_id=place1_id,
        price=450.0,
        start_time="12:00",
        end_time="16:00",
        description="Грибной суп, бефстроганов с макаронами, чай",
        weekday=3  # Среда
    )
    
    # Четверг
    await db.add_business_lunch(
        place_id=place1_id,
        price=470.0,
        start_time="12:00",
        end_time="16:00",
        description="Щи, тефтели с гречкой, компот",
        weekday=4  # Четверг
    )
    
    # Пятница
    await db.add_business_lunch(
        place_id=place1_id,
        price=490.0,
        start_time="12:00",
        end_time="16:00",
        description="Окрошка, стейк с овощами, лимонад",
        weekday=5  # Пятница
    )
    
    # Обычные позиции меню
    await db.add_menu_item(
        place_id=place1_id,
        name="Карбонара",
        price=320.0,
        category="паста",
        description="Классическая итальянская паста с беконом и сливочным соусом"
    )
    
    await db.add_menu_item(
        place_id=place1_id,
        name="Цезарь с курицей",
        price=280.0,
        category="салат",
        description="Салат с курицей, сыром пармезан и соусом цезарь"
    )
    
    # 2. Кафе с одинаковым бизнес-ланчем на каждый день
    place2_id = await db.add_place(
        name="Кафе 'У Петровича'",
        address="пр. Ленина, 42",
        category="кафе",
        admin_comment="Недорогое заведение с домашней кухней, бизнес-ланч одинаковый каждый день"
    )
    
    # Каждый день один и тот же бизнес-ланч
    await db.add_business_lunch(
        place_id=place2_id,
        price=350.0,
        start_time="11:30",
        end_time="15:00",
        description="Салат на выбор, суп дня, горячее на выбор, компот",
        weekday=0  # 0 означает каждый день
    )
    
    await db.add_menu_item(
        place_id=place2_id,
        name="Борщ",
        price=180.0,
        category="суп",
        description="Традиционный борщ со сметаной"
    )
    
    await db.add_menu_item(
        place_id=place2_id,
        name="Пельмени",
        price=250.0,
        category="горячее",
        description="Домашние пельмени со сметаной"
    )
    
    # 3. Кальянная с бизнес-ланчем на будние дни и выходные
    place3_id = await db.add_place(
        name="Кальянная 'Дымок'",
        address="ул. Революции, 15",
        category="кальянная",
        admin_comment="Атмосферное место для отдыха с друзьями, особые бизнес-ланчи по выходным"
    )
    
    # Бизнес-ланч на будние дни (пн-пт)
    for weekday in range(1, 6):  # 1-5 (пн-пт)
        await db.add_business_lunch(
            place_id=place3_id,
            price=500.0,
            start_time="13:00",
            end_time="17:00",
            description="Суп дня, горячее блюдо, десерт, чай",
            weekday=weekday
        )
    
    # Особый бизнес-ланч на выходные
    for weekday in range(6, 8):  # 6-7 (сб-вс)
        await db.add_business_lunch(
            place_id=place3_id,
            price=650.0,
            start_time="14:00",
            end_time="18:00",
            description="Салат, суп, стейк, десерт, вино",
            weekday=weekday
        )
    
    await db.add_menu_item(
        place_id=place3_id,
        name="Фруктовый кальян",
        price=1200.0,
        category="кальян",
        description="Кальян на фруктовых вкусах"
    )
    
    await db.add_menu_item(
        place_id=place3_id,
        name="Ягодный кальян",
        price=1300.0,
        category="кальян",
        description="Кальян на ягодных вкусах"
    )
    
    # 4. Пивной ресторан без бизнес-ланча
    place4_id = await db.add_place(
        name="Пивной ресторан 'Хмель'",
        address="ул. Барная, 7",
        category="пивной ресторан",
        admin_comment="Большой выбор пива и закусок"
    )
    
    await db.add_menu_item(
        place_id=place4_id,
        name="Светлое нефильтрованное",
        price=250.0,
        category="пиво",
        description="Светлое нефильтрованное пиво местного производства"
    )
    
    await db.add_menu_item(
        place_id=place4_id,
        name="Тёмное крафтовое",
        price=320.0,
        category="пиво",
        description="Тёмное крафтовое пиво с карамельными нотками"
    )
    
    await db.add_menu_item(
        place_id=place4_id,
        name="Колбаски гриль",
        price=450.0,
        category="закуска",
        description="Ассорти из колбасок на гриле с соусами"
    )
    
    # 5. Ещё одна кальянная
    place5_id = await db.add_place(
        name="Lounge bar 'Облако'",
        address="ул. Комсомольская, 23",
        category="кальянная",
        admin_comment="Модное место с приятной атмосферой и качественными кальянами"
    )
    
    await db.add_menu_item(
        place_id=place5_id,
        name="Премиум кальян",
        price=1500.0,
        category="кальян",
        description="Премиум кальян на элитных вкусах"
    )
    
    await db.add_menu_item(
        place_id=place5_id,
        name="Авторский кальян",
        price=1800.0,
        category="кальян",
        description="Авторский кальян от шеф-кальянщика"
    )
    
    await db.add_menu_item(
        place_id=place5_id,
        name="Фруктовая тарелка",
        price=600.0,
        category="закуска",
        description="Ассорти из сезонных фруктов"
    )
    
    # 6. Ресторан с сезонным бизнес-ланчем
    place6_id = await db.add_place(
        name="Ресторан 'Маэстро'",
        address="пр. Победы, 112",
        category="ресторан",
        admin_comment="Ресторан итальянской кухни с живой музыкой по вечерам и бизнес-ланчем ежедневно"
    )
    
    # Общий бизнес-ланч на каждый день
    await db.add_business_lunch(
        place_id=place6_id,
        price=550.0,
        start_time="12:00",
        end_time="15:30",
        description="Салат, суп, пицца или паста на выбор, десерт, кофе",
        weekday=0  # Каждый день
    )
    
    await db.add_menu_item(
        place_id=place6_id,
        name="Пицца Маргарита",
        price=450.0,
        category="пицца",
        description="Классическая итальянская пицца с томатами и моцареллой"
    )
    
    await db.add_menu_item(
        place_id=place6_id,
        name="Лазанья",
        price=380.0,
        category="горячее",
        description="Традиционная итальянская лазанья с мясным соусом"
    )
    
    # Добавляем отзывы
    print("Добавление тестовых отзывов...")
    
    # Отзывы для первого ресторана
    await db.add_review(user_id=123456789, place_id=place1_id, rating=5, 
                       comment="Отличный бизнес-ланч, всегда свежие блюда")
    await db.add_review(user_id=987654321, place_id=place1_id, rating=4, 
                       comment="Вкусно, но иногда приходится ждать")
    
    # Отзывы для второго ресторана
    await db.add_review(user_id=123456789, place_id=place2_id, rating=3, 
                       comment="Неплохо за свои деньги")
    await db.add_review(user_id=555555555, place_id=place2_id, rating=5, 
                       comment="Очень вкусно и по-домашнему")
    
    # Отзывы для кальянной
    await db.add_review(user_id=777777777, place_id=place3_id, rating=5, 
                       comment="Лучшие кальяны в городе!")
    await db.add_review(user_id=888888888, place_id=place3_id, rating=4, 
                       comment="Хорошие кальяны, приятная атмосфера")
    
    print("База данных успешно заполнена тестовыми данными!")

if __name__ == "__main__":
    asyncio.run(seed_database()) 