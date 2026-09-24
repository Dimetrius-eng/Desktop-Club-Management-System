import pymysql # Ми підключаємо бібліотеку для роботи з MySQL/MariaDB. Це один з найпопулярніших конекторів для Python.
from pymysql.cursors import DictCursor

"""
 замовчуванням бази даних повертають результати у вигляді кортежів (tuples), наприклад ('Ivan', 'Admin').
DictCursor змінює цю поведінку так, щоб кожен рядок повертався як словник: {'username': 'Ivan', 'role': 'Admin'}.
Це робить код читабельнішим, адже ми звертаємось до даних за назвою колонки, а не за індексом
"""

# Тут ми створюємо клас DatabaseManager. У методі __init__ задаються базові налаштування
class DatabaseManager:
    def __init__(self):
        self.host = 'localhost'  # Вказує, що база даних знаходиться на тому ж комп'ютері, що й програма

        # Облікові дані для підключення
        self.database = 'sports_club'
        self.user = 'root'
        self.password = ''

        # На старті з'єднання немає. Зберігаючи його в атрибуті класу, ми можемо керувати ним з будь-якого іншого методу
        self.connection = None

    # Метод connect спробує встановити з'єднання. Ми використовуємо блок try...except, щоб програма не "впала", якщо база даних вимкнена
    """
    charset='utf8mb4' - дуже важливий рядок. Він гарантує, що база дани правильно розумітиме українську мову,
    специфічні символи та навіть емодзі(на відміну від звичайного utf8).
    """
    def connect(self):
        try:
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor  # Саме тут ми застосовуємо імпортований раніше курсор для повернення словників
            )
            return True
        except Exception as e:
            print(f"Помилка підключення до БД: {e}")
            return False

    """
    Метод disconnect перевіряє, чи існує об'єкт з'єднання і чи воно досі відкрите. Якщо так — закриває його.
    Це звільняє ресурси комп'ютера та сервера бази даних
    """
    def disconnect(self):
        if self.connection and self.connection.open:
            self.connection.close()

    # Цей метод призначений для запитів типу INSERT, UPDATE та DELETE (ті, що змінюють дані).
    def execute_query(self, query, params=None):
        if self.connect():
            try:
                # Використання контекстного менеджера with гарантує, що курсор буде закрито автоматично після виконання блоку
                with self.connection.cursor() as cursor:
                    # Ми передаємо параметри окремо від тексту запиту (query)
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)
                self.connection.commit() # Бази даних використовують транзакції. Зміни не запишуться на диск, поки ми явно не викличемо commit()
                return True
            except Exception as e:
                print(f"Помилка виконання запиту: {e}")
                return False
            # Блок finally виконається у будь-якому разі (і при успіху, і при помилці),
            # гарантуючи, що з'єднання буде закрито і не виникне витоку пам'яті.
            finally:

                self.disconnect()

    """
    Цей метод дуже схожий на попередній, але використовується виключно для SELECT запитів.
    Головна відмінність: тут немає commit() (оскільки ми нічого не змінюємо), натомість є result = cursor.fetchall(),
    який зчитує всі знайдені рядки з бази та повертає їх як список словників
    """

    def fetch_data(self, query, params=None):
        if self.connect():
            try:
                with self.connection.cursor() as cursor:
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)
                    result = cursor.fetchall()
                    return result
            except Exception as e:
                print(f"Помилка отримання даних: {e}")
                return None
            finally:
                self.disconnect()
            # Тестовий блок

# Тестовий блок
"""
Гарантує, що тестовий код виконається ТІЛЬКИ якщо ми запустимо безпосередньо файл db_manager.py.
Якщо ж ми імпортуємо цей файл у main.py, тестовий блок буде проігноровано
"""
if __name__ == "__main__":
    db = DatabaseManager()
    users = db.fetch_data("SELECT username, role FROM Users")
    if users is not None:
        print("З'єднання успішне! Користувачі в базі:")
        for u in users:
            print(f"- Логін: {u['username']}, Роль: {u['role']}")
    else:
        print("Не вдалося підключитися. Перевір пароль (можливо, треба порожній'')!")

"""
Цей модуль є надійним ядром для спілкування з базою. Потрібно звернути увагу на те, як реалізовані методи execute_query та fetch_data.
Вони приймають sql-запит (query) та окремо параметри до нього (params). Це головний та найважливіший захист від SQL-ін'єкцій.
Коли ми передаємо параметри окремо, бібліотека pymysql безпечно екранує їх і сприймає виключно як дані, а не як частину виконуваного коду.
Це не дозволить зловмиснику зламати базу (або обійти пароль), ввівши в поле логіна щось хитре на кшталт ' OR 1=1 --.
"""

