import aiosqlite
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date

class Database:
    def __init__(self, db_name: str = "lunch_hunter.db"):
        self.db_name = db_name
        
    async def create_tables(self):
        """Создает необходимые таблицы в базе данных"""
        async with aiosqlite.connect(self.db_name) as db:
            # Таблица пользователей
            await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                city TEXT NOT NULL,
                is_admin BOOLEAN NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Таблица заведений
            await db.execute('''
            CREATE TABLE IF NOT EXISTS places (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT NOT NULL,
                category TEXT NOT NULL,
                city TEXT NOT NULL,
                photo_id TEXT,
                admin_comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Таблица бизнес-ланчей
            await db.execute('''
            CREATE TABLE IF NOT EXISTS business_lunches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                place_id INTEGER NOT NULL,
                weekday INTEGER NOT NULL DEFAULT 0,
                price REAL NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                description TEXT,
                FOREIGN KEY (place_id) REFERENCES places(id) ON DELETE CASCADE
            )
            ''')
            
            # Таблица позиций меню
            await db.execute('''
            CREATE TABLE IF NOT EXISTS menu_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                place_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                FOREIGN KEY (place_id) REFERENCES places(id) ON DELETE CASCADE
            )
            ''')
            
            # Таблица отзывов
            await db.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                place_id INTEGER NOT NULL,
                rating INTEGER NOT NULL,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (place_id) REFERENCES places(id) ON DELETE CASCADE
            )
            ''')
            
            await db.commit()
    
    async def add_user(self, user_id: int, username: Optional[str], city: str) -> int:
        """Добавляет или обновляет пользователя в базе данных"""
        async with aiosqlite.connect(self.db_name) as db:
            # Проверяем, существует ли пользователь
            cursor = await db.execute('SELECT user_id, is_admin FROM users WHERE user_id = ?', (user_id,))
            existing_user = await cursor.fetchone()
            
            if existing_user:
                # Обновляем существующего пользователя, но сохраняем статус администратора
                is_admin = existing_user[1]
                await db.execute('''
                UPDATE users SET username = ?, city = ? WHERE user_id = ?
                ''', (username, city, user_id))
            else:
                # Добавляем нового пользователя
                await db.execute('''
                INSERT INTO users (user_id, username, city, is_admin) VALUES (?, ?, ?, 0)
                ''', (user_id, username, city))
            
            await db.commit()
            return user_id
    
    async def set_admin_status(self, user_id: int, is_admin: bool) -> bool:
        """Устанавливает статус администратора для пользователя (только для ручного вызова)"""
        async with aiosqlite.connect(self.db_name) as db:
            # Проверяем, существует ли пользователь
            cursor = await db.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
            existing_user = await cursor.fetchone()
            
            if not existing_user:
                return False
            
            # Обновляем статус администратора
            await db.execute('''
            UPDATE users SET is_admin = ? WHERE user_id = ?
            ''', (1 if is_admin else 0, user_id))
            
            await db.commit()
            return True
    
    async def is_admin(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь администратором"""
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute('''
            SELECT is_admin FROM users WHERE user_id = ?
            ''', (user_id,))
            
            row = await cursor.fetchone()
            return bool(row and row[0])
    
    async def get_user_city(self, user_id: int) -> Optional[str]:
        """Получает город пользователя"""
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute('''
            SELECT city FROM users WHERE user_id = ?
            ''', (user_id,))
            
            row = await cursor.fetchone()
            return row[0] if row else None
    
    async def add_place(self, name: str, address: str, category: str, city: str,
                        photo_id: Optional[str] = None, 
                        admin_comment: Optional[str] = None) -> int:
        """Добавляет новое заведение в базу данных"""
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute('''
            INSERT INTO places (name, address, category, city, photo_id, admin_comment)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, address, category, city, photo_id, admin_comment))
            
            await db.commit()
            return cursor.lastrowid
    
    async def add_business_lunch(self, place_id: int, price: float, 
                                start_time: str, end_time: str, 
                                description: Optional[str] = None,
                                weekday: int = 0) -> int:
        """
        Добавляет информацию о бизнес-ланче для заведения
        
        Args:
            place_id: ID заведения
            price: Цена бизнес-ланча
            start_time: Время начала
            end_time: Время окончания
            description: Описание бизнес-ланча
            weekday: День недели (0 - каждый день, 1 - пн, 2 - вт, и т.д.)
        """
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute('''
            INSERT INTO business_lunches (place_id, price, start_time, end_time, description, weekday)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (place_id, price, start_time, end_time, description, weekday))
            
            await db.commit()
            return cursor.lastrowid
    
    async def add_menu_item(self, place_id: int, name: str, price: float, 
                           category: str, description: Optional[str] = None) -> int:
        """Добавляет позицию меню для заведения"""
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute('''
            INSERT INTO menu_items (place_id, name, price, category, description)
            VALUES (?, ?, ?, ?, ?)
            ''', (place_id, name, price, category, description))
            
            await db.commit()
            return cursor.lastrowid
    
    async def add_review(self, user_id: int, place_id: int, rating: int, 
                        comment: Optional[str] = None) -> int:
        """Добавляет отзыв о заведении"""
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute('''
            INSERT INTO reviews (user_id, place_id, rating, comment)
            VALUES (?, ?, ?, ?)
            ''', (user_id, place_id, rating, comment))
            
            await db.commit()
            return cursor.lastrowid
    
    async def get_business_lunches(self, city: str, limit: int = 10, offset: int = 0, weekday: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Получает список заведений с бизнес-ланчами
        
        Args:
            city: Город
            limit: Ограничение количества результатов
            offset: Смещение для пагинации
            weekday: Конкретный день недели (1-7) или None для текущего дня
        """
        # Если weekday не указан, используем текущий день недели
        if weekday is None:
            weekday = datetime.now().isoweekday()  # 1 - пн, 2 - вт, и т.д.
        
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
            SELECT p.id, p.name, p.address, p.city, p.photo_id, p.admin_comment,
                   bl.price, bl.start_time, bl.end_time, bl.description, bl.weekday
            FROM places p
            JOIN business_lunches bl ON p.id = bl.place_id
            WHERE (bl.weekday = ? OR bl.weekday = 0) AND p.city = ?
            GROUP BY p.id
            ORDER BY p.name
            LIMIT ? OFFSET ?
            ''', (weekday, city, limit, offset))
            
            rows = await cursor.fetchall()
            result = []
            for row in rows:
                result.append(dict(row))
            return result
    
    async def search_places_by_menu(self, query: str, city: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Поиск заведений по позициям меню"""
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
            SELECT DISTINCT p.id, p.name, p.address, p.city, p.photo_id, p.admin_comment
            FROM places p
            JOIN menu_items mi ON p.id = mi.place_id
            WHERE (mi.name LIKE ? OR mi.category LIKE ?) AND p.city = ?
            ORDER BY p.name
            LIMIT ? OFFSET ?
            ''', (f'%{query}%', f'%{query}%', city, limit, offset))
            
            rows = await cursor.fetchall()
            result = []
            for row in rows:
                result.append(dict(row))
            return result
    
    async def get_place_by_id(self, place_id: int) -> Optional[Dict[str, Any]]:
        """Получает информацию о заведении по ID"""
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
            SELECT * FROM places WHERE id = ?
            ''', (place_id,))
            
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    async def get_business_lunch_by_place_id(self, place_id: int, weekday: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Получает информацию о бизнес-ланче заведения на определенный день недели
        
        Args:
            place_id: ID заведения
            weekday: День недели (1-7) или None для текущего дня
        """
        # Если weekday не указан, используем текущий день недели
        if weekday is None:
            weekday = datetime.now().isoweekday()  # 1 - пн, 2 - вт, и т.д.
        
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            # Сначала пытаемся найти бизнес-ланч для конкретного дня недели
            cursor = await db.execute('''
            SELECT * FROM business_lunches 
            WHERE place_id = ? AND weekday = ?
            ''', (place_id, weekday))
            
            row = await cursor.fetchone()
            if row:
                lunch = dict(row)
                lunch['weekday_name'] = self._get_weekday_name(weekday)
                return lunch
            
            # Если для конкретного дня нет, ищем бизнес-ланч, доступный каждый день
            cursor = await db.execute('''
            SELECT * FROM business_lunches 
            WHERE place_id = ? AND weekday = 0
            ''', (place_id,))
            
            row = await cursor.fetchone()
            if row:
                lunch = dict(row)
                lunch['weekday_name'] = "Каждый день"
                return lunch
            
            return None
    
    async def get_business_lunches_for_all_days(self, place_id: int) -> List[Dict[str, Any]]:
        """
        Получает информацию о бизнес-ланчах заведения для всех дней недели
        
        Args:
            place_id: ID заведения
        """
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
            SELECT * FROM business_lunches 
            WHERE place_id = ?
            ORDER BY weekday
            ''', (place_id,))
            
            rows = await cursor.fetchall()
            result = []
            for row in rows:
                lunch = dict(row)
                lunch['weekday_name'] = self._get_weekday_name(lunch['weekday'])
                result.append(lunch)
            return result
    
    async def get_menu_items_by_place_id(self, place_id: int) -> List[Dict[str, Any]]:
        """Получает позиции меню заведения"""
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
            SELECT * FROM menu_items WHERE place_id = ?
            ORDER BY category, name
            ''', (place_id,))
            
            rows = await cursor.fetchall()
            result = []
            for row in rows:
                result.append(dict(row))
            return result
    
    async def get_reviews_by_place_id(self, place_id: int) -> List[Dict[str, Any]]:
        """Получает отзывы о заведении"""
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
            SELECT * FROM reviews WHERE place_id = ?
            ORDER BY created_at DESC
            ''', (place_id,))
            
            rows = await cursor.fetchall()
            result = []
            for row in rows:
                result.append(dict(row))
            return result
    
    async def count_business_lunches(self, city: str, weekday: Optional[int] = None) -> int:
        """
        Подсчитывает общее количество заведений с бизнес-ланчами
        
        Args:
            city: Город
            weekday: День недели (1-7) или None для текущего дня
        """
        # Если weekday не указан, используем текущий день недели
        if weekday is None:
            weekday = datetime.now().isoweekday()  # 1 - пн, 2 - вт, и т.д.
        
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute('''
            SELECT COUNT(DISTINCT p.id)
            FROM places p
            JOIN business_lunches bl ON p.id = bl.place_id
            WHERE (bl.weekday = ? OR bl.weekday = 0) AND p.city = ?
            ''', (weekday, city))
            
            count = await cursor.fetchone()
            return count[0] if count else 0
    
    async def count_search_results(self, query: str, city: str) -> int:
        """Подсчитывает количество результатов поиска"""
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute('''
            SELECT COUNT(DISTINCT p.id)
            FROM places p
            JOIN menu_items mi ON p.id = mi.place_id
            WHERE (mi.name LIKE ? OR mi.category LIKE ?) AND p.city = ?
            ''', (f'%{query}%', f'%{query}%', city))
            
            count = await cursor.fetchone()
            return count[0] if count else 0
    
    async def get_places_for_admin(self, city: str) -> List[Dict[str, Any]]:
        """Получает список всех заведений для администратора"""
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
            SELECT * FROM places
            WHERE city = ?
            ORDER BY name
            ''', (city,))
            
            rows = await cursor.fetchall()
            result = []
            for row in rows:
                result.append(dict(row))
            return result
    
    def _get_weekday_name(self, weekday: int) -> str:
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
    
    async def get_menu_categories_by_place_id(self, place_id: int) -> List[str]:
        """Получает список уникальных категорий меню заведения"""
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute('''
            SELECT DISTINCT category FROM menu_items
            WHERE place_id = ?
            ORDER BY category
            ''', (place_id,))
            
            rows = await cursor.fetchall()
            return [row[0] for row in rows] if rows else []

    async def get_menu_items_by_category(self, place_id: int, category: str) -> List[Dict[str, Any]]:
        """Получает позиции меню заведения по категории"""
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
            SELECT * FROM menu_items
            WHERE place_id = ? AND category = ?
            ORDER BY name
            ''', (place_id, category))
            
            rows = await cursor.fetchall()
            result = []
            for row in rows:
                result.append(dict(row))
            return result 