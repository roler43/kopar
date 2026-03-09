import sqlite3
import time
from config import DB_FILE, SUBSCRIPTION_DURATION

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        # Таблица пользователей
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                joined_date INTEGER,
                last_flood INTEGER DEFAULT 0,
                floods_count INTEGER DEFAULT 0,
                is_admin INTEGER DEFAULT 0,
                is_banned INTEGER DEFAULT 0,
                subscription_type TEXT DEFAULT 'none',
                subscription_until INTEGER DEFAULT 0,
                total_payments REAL DEFAULT 0,
                free_trial_used INTEGER DEFAULT 0,
                name_checked INTEGER DEFAULT 0
            )
        ''')
        
        # Таблица платежей
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                invoice_id TEXT UNIQUE,
                amount REAL,
                currency TEXT,
                subscription_type TEXT,
                status TEXT,
                created_at INTEGER,
                paid_at INTEGER
            )
        ''')
        
        # Таблица обращений в поддержку
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS support_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message TEXT,
                created_at INTEGER,
                status TEXT DEFAULT 'open',
                admin_reply TEXT,
                replied_at INTEGER
            )
        ''')
        
        # Таблица промокодов
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS promo_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                hours INTEGER,
                max_uses INTEGER,
                used_count INTEGER DEFAULT 0,
                created_by INTEGER,
                created_at INTEGER,
                expires_at INTEGER
            )
        ''')
        
        # Таблица использованных промокодов
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS promo_uses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                promo_id INTEGER,
                user_id INTEGER,
                used_at INTEGER,
                FOREIGN KEY (promo_id) REFERENCES promo_codes(id)
            )
        ''')
        
        self.conn.commit()
    
    # Проверка имени на наличие бота
    def check_name_for_bot(self, user_id, first_name):
        """Проверяет, есть ли в имени юзера бот и выдает бесплатную подписку"""
        self.cursor.execute('SELECT free_trial_used, name_checked FROM users WHERE user_id = ?', (user_id,))
        result = self.cursor.fetchone()
        
        if not result:
            return False
        
        free_trial_used, name_checked = result
        
        # Если уже получал бесплатную подписку или имя уже проверяли
        if free_trial_used == 1 or name_checked == 1:
            print(f"Пользователь {user_id} уже получал подписку или имя проверено")
            return False
        
        from config import BOT_USERNAME
        print(f"Проверка имени {first_name} на наличие {BOT_USERNAME}")
        
        if first_name and BOT_USERNAME in first_name:
            print(f"Найдено совпадение! Выдаем подписку")
            # Выдаем бесплатную подписку на 3 часа
            from config import FREE_TRIAL_HOURS
            current_time = int(time.time())
            until = current_time + (FREE_TRIAL_HOURS * 3600)
            
            self.cursor.execute('''
                UPDATE users 
                SET subscription_type = 'trial', 
                    subscription_until = ?,
                    free_trial_used = 1,
                    name_checked = 1
                WHERE user_id = ?
            ''', (until, user_id))
            self.conn.commit()
            return True
        
        print(f"Бот не найден в имени")
        # Отмечаем что имя проверили, но подписку не выдали
        self.cursor.execute('UPDATE users SET name_checked = 1 WHERE user_id = ?', (user_id,))
        self.conn.commit()
        return False
    
    # Основные методы для пользователей
    def add_user(self, user_id, username, first_name, last_name):
        self.cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, joined_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, int(time.time())))
        self.conn.commit()
        
        # Проверяем имя при регистрации
        self.check_name_for_bot(user_id, first_name)
    
    def get_user(self, user_id):
        self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return self.cursor.fetchone()
    
    def update_user_name(self, user_id, first_name):
        """Обновляет имя пользователя и проверяет наличие бота"""
        self.cursor.execute('UPDATE users SET first_name = ? WHERE user_id = ?', (first_name, user_id))
        self.conn.commit()
        # Проверяем имя после обновления
        return self.check_name_for_bot(user_id, first_name)
    
    # Методы для подписок
    def get_subscription_type(self, user_id):
        self.cursor.execute('SELECT subscription_type, subscription_until FROM users WHERE user_id = ?', (user_id,))
        result = self.cursor.fetchone()
        if not result:
            return 'none', 0
        
        sub_type, sub_until = result
        if sub_type != 'none' and sub_type != 'forever' and sub_type != 'trial' and sub_until < int(time.time()):
            # Подписка истекла
            self.cursor.execute('UPDATE users SET subscription_type = ? WHERE user_id = ?', ('none', user_id))
            self.conn.commit()
            return 'none', 0
        
        return sub_type, sub_until
    
    def update_subscription(self, user_id, days, sub_type):
        current_time = int(time.time())
        if sub_type == 'forever':
            # +100 лет для вечной подписки
            until = current_time + (365 * 24 * 3600 * 100)
        else:
            until = current_time + (days * 24 * 3600)
        
        self.cursor.execute('''
            UPDATE users 
            SET subscription_type = ?, subscription_until = ? 
            WHERE user_id = ?
        ''', (sub_type, until, user_id))
        self.conn.commit()
    
    def add_subscription_hours(self, user_id, hours):
        """Добавляет часы к существующей подписке"""
        current_time = int(time.time())
        sub_type, sub_until = self.get_subscription_type(user_id)
        
        if sub_type == 'none':
            # Если нет подписки, создаем новую
            until = current_time + (hours * 3600)
            self.cursor.execute('''
                UPDATE users 
                SET subscription_type = 'trial', subscription_until = ? 
                WHERE user_id = ?
            ''', (until, user_id))
        elif sub_type == 'forever':
            # Вечная подписка остается вечной
            pass
        else:
            # Добавляем часы к существующей
            if sub_until < current_time:
                new_until = current_time + (hours * 3600)
            else:
                new_until = sub_until + (hours * 3600)
            
            self.cursor.execute('''
                UPDATE users 
                SET subscription_until = ? 
                WHERE user_id = ?
            ''', (new_until, user_id))
        
        self.conn.commit()
    
    def can_flood(self, user_id):
        self.cursor.execute('''
            SELECT last_flood, subscription_type, subscription_until 
            FROM users WHERE user_id = ?
        ''', (user_id,))
        result = self.cursor.fetchone()
        
        if not result or result[0] == 0:
            return True, 0, 'none'
        
        last_flood, sub_type, sub_until = result
        
        # Проверяем актуальность подписки
        if sub_type != 'none' and sub_type != 'forever' and sub_until < int(time.time()):
            sub_type = 'none'
        
        # Определяем кулдаун в зависимости от подписки
        if sub_type == 'forever':
            cooldown = 0  # Без кулдауна
        elif sub_type in ['1day', '7days', '30days', 'trial']:
            cooldown = 60  # 1 минута для VIP и триала
        else:
            cooldown = 300  # 5 минут для обычных
        
        time_passed = int(time.time()) - last_flood
        if time_passed >= cooldown:
            return True, 0, sub_type
        else:
            remaining = cooldown - time_passed
            return False, remaining, sub_type
    
    def update_last_flood(self, user_id):
        self.cursor.execute('''
            UPDATE users 
            SET last_flood = ?, floods_count = floods_count + 1 
            WHERE user_id = ?
        ''', (int(time.time()), user_id))
        self.conn.commit()
    
    # Методы для промокодов
    def create_promo(self, code, hours, max_uses, created_by, expires_at=None):
        """Создает новый промокод"""
        try:
            self.cursor.execute('''
                INSERT INTO promo_codes (code, hours, max_uses, created_by, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (code, hours, max_uses, created_by, int(time.time()), expires_at))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_promo(self, code):
        """Получает информацию о промокоде"""
        self.cursor.execute('SELECT * FROM promo_codes WHERE code = ?', (code,))
        return self.cursor.fetchone()
    
    def use_promo(self, code, user_id):
        """Активирует промокод для пользователя"""
        promo = self.get_promo(code)
        if not promo:
            return False, "Промокод не найден"
        
        promo_id, promo_code, hours, max_uses, used_count, created_by, created_at, expires_at = promo
        
        # Проверяем срок действия
        if expires_at and expires_at < int(time.time()):
            return False, "Промокод истек"
        
        # Проверяем лимит использований
        if max_uses > 0 and used_count >= max_uses:
            return False, "Промокод больше не действителен"
        
        # Проверяем, не использовал ли пользователь этот промокод
        self.cursor.execute('SELECT * FROM promo_uses WHERE promo_id = ? AND user_id = ?', (promo_id, user_id))
        if self.cursor.fetchone():
            return False, "Вы уже использовали этот промокод"
        
        # Начисляем часы подписки
        self.add_subscription_hours(user_id, hours)
        
        # Записываем использование
        self.cursor.execute('''
            INSERT INTO promo_uses (promo_id, user_id, used_at)
            VALUES (?, ?, ?)
        ''', (promo_id, user_id, int(time.time())))
        
        # Увеличиваем счетчик использований
        self.cursor.execute('''
            UPDATE promo_codes SET used_count = used_count + 1 WHERE id = ?
        ''', (promo_id,))
        
        self.conn.commit()
        return True, f"Промокод активирован! Добавлено {hours} часов подписки"
    
    def get_all_promos(self):
        """Получает все промокоды"""
        self.cursor.execute('SELECT * FROM promo_codes ORDER BY created_at DESC')
        return self.cursor.fetchall()
    
    # Методы для платежей
    def add_payment(self, user_id, invoice_id, amount, currency, subscription_type):
        self.cursor.execute('''
            INSERT INTO payments (user_id, invoice_id, amount, currency, subscription_type, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, invoice_id, amount, currency, subscription_type, 'pending', int(time.time())))
        self.conn.commit()
    
    def update_payment_status(self, invoice_id, status):
        self.cursor.execute('''
            UPDATE payments 
            SET status = ?, paid_at = ? 
            WHERE invoice_id = ?
        ''', (status, int(time.time()) if status == 'paid' else None, invoice_id))
        self.conn.commit()
        
        if status == 'paid':
            # Начисляем подписку
            self.cursor.execute('''
                SELECT user_id, subscription_type FROM payments WHERE invoice_id = ?
            ''', (invoice_id,))
            result = self.cursor.fetchone()
            if result:
                user_id, sub_type = result
                
                days = SUBSCRIPTION_DURATION.get(sub_type, 30)
                self.update_subscription(user_id, days, sub_type)
                
                # Обновляем общую сумму платежей
                amount = self.cursor.execute('SELECT amount FROM payments WHERE invoice_id = ?', (invoice_id,)).fetchone()[0]
                self.cursor.execute('''
                    UPDATE users SET total_payments = total_payments + ? WHERE user_id = ?
                ''', (amount, user_id))
                self.conn.commit()
    
    def get_payment(self, invoice_id):
        self.cursor.execute('SELECT * FROM payments WHERE invoice_id = ?', (invoice_id,))
        return self.cursor.fetchone()
    
    # Методы для поддержки
    def create_ticket(self, user_id, message):
        self.cursor.execute('''
            INSERT INTO support_tickets (user_id, message, created_at)
            VALUES (?, ?, ?)
        ''', (user_id, message, int(time.time())))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_ticket(self, ticket_id):
        self.cursor.execute('SELECT * FROM support_tickets WHERE id = ?', (ticket_id,))
        return self.cursor.fetchone()
    
    def get_open_tickets(self):
        self.cursor.execute('SELECT * FROM support_tickets WHERE status = "open" ORDER BY created_at DESC')
        return self.cursor.fetchall()
    
    def reply_to_ticket(self, ticket_id, admin_reply):
        self.cursor.execute('''
            UPDATE support_tickets 
            SET status = 'closed', admin_reply = ?, replied_at = ? 
            WHERE id = ?
        ''', (admin_reply, int(time.time()), ticket_id))
        self.conn.commit()
    
    # Статистика для админа
    def get_stats(self):
        self.cursor.execute('SELECT COUNT(*) FROM users')
        users_total = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT SUM(floods_count) FROM users')
        floods_total = self.cursor.fetchone()[0] or 0
        
        self.cursor.execute('SELECT COUNT(*) FROM users WHERE subscription_type != "none"')
        vip_total = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT COUNT(*) FROM users WHERE free_trial_used = 1')
        trial_users = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT SUM(total_payments) FROM users')
        total_income = self.cursor.fetchone()[0] or 0
        
        self.cursor.execute('SELECT COUNT(*) FROM support_tickets WHERE status = "open"')
        open_tickets = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT COUNT(*) FROM promo_codes')
        promos_total = self.cursor.fetchone()[0]
        
        return {
            'users_total': users_total,
            'floods_total': floods_total,
            'vip_total': vip_total,
            'trial_users': trial_users,
            'total_income': total_income,
            'open_tickets': open_tickets,
            'promos_total': promos_total
        }
    
    def get_all_users(self):
        self.cursor.execute('SELECT user_id FROM users')
        return [row[0] for row in self.cursor.fetchall()]
    
    def is_banned(self, user_id):
        self.cursor.execute('SELECT is_banned FROM users WHERE user_id = ?', (user_id,))
        result = self.cursor.fetchone()
        return result and result[0] == 1

# Создаем экземпляр базы данных для импорта
db = Database()
