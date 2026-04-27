import psycopg2
import json 
import os

# Подключение к базе данных
conn = psycopg2.connect(
    dbname="postgres",  
    user="postgres",   
    password="alibek08",  
    host="localhost",          
)

cursor = conn.cursor()

def add_contact_with_details():
    try:
        print("\nДобавление нового контакта")
        name = input("Имя: ")
        email = input("Email: ")
        birthday = input("День рождения (г-д-м) ")
        
        # 1. Получаем список групп (теперь колонка называется id)
        cursor.execute("SELECT id, name FROM groups")
        groups_list = cursor.fetchall()
        
        print("\nДоступные группы:")
        for g in groups_list:
            print(f"{g[0]} - {g[1]}") # g[0] это id, g[1] это name
            
        selected_group_id = input("Выберите ID группы: ")

        cursor.execute(
            """INSERT INTO phonetry2 (user_name, email, birthday, group_id) 
               VALUES (%s, %s, %s, %s) RETURNING user_id""",
            (name, email, birthday if birthday else None, selected_group_id)
        )
        user_id = cursor.fetchone()[0]

        #Добавляем телефоны в таблицу phones
        while True:
            phone_num = input("Введите номер телефона: ")
            print("Типы: home, work, mobile")
            phone_type = input("Выберите тип: ").lower()
            
            if phone_type not in ['home', 'work', 'mobile']:
                phone_type = 'mobile'
            
            cursor.execute(
                "INSERT INTO phones (contact_id, phone, type) VALUES (%s, %s, %s)",
                (user_id, phone_num, phone_type)
            )
            
            more = input("Добавить еще один номер? (y/n): ")
            if more.lower() != 'y':
                break

        conn.commit()
        print(f"Контакт {name} успешно добавлен!")
        
    except Exception as e:
        conn.rollback()
        print(f"Ошибка в процессе добавления: {e}")
def show_all_detailed():
    query = """
    SELECT p.user_name, p.email, g.name, ph.phone, ph.type
    FROM phonetry2 p
    LEFT JOIN groups g ON p.group_id = g.id
    LEFT JOIN phones ph ON p.user_id = ph.contact_id
    ORDER BY p.user_name;
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    print("\n--- СПИСОК КОНТАКТОВ ---")
    for row in rows:
        print(f"Имя: {row[0]} | Email: {row[1]} | Группа: {row[2]} | {row[3]} ({row[4]})")


#Добавление или обновление одного контакта
def insert_or_update_user(user_name, numberph):
    try:
        cursor.execute("SELECT COUNT(*) FROM phonetry2 WHERE user_name = %s", (user_name,))
        count = cursor.fetchone()[0]

        if count > 0:
            cursor.execute("UPDATE phonetry2 SET numberph = %s WHERE user_name = %s", (numberph, user_name))
            print(f"Контакт {user_name} обновлён.")
        else:
            cursor.execute("INSERT INTO phonetry2 (user_name, numberph) VALUES (%s, %s)", (user_name, numberph))
            print(f"Контакт {user_name} добавлен.")

        conn.commit()
    except Exception as e:
        print(f"Ошибка при добавлении/обновлении контакта: {e}")
        conn.rollback()

#Поиск по шаблону
def search_by_pattern(pattern):
    try:
        cursor.execute(
            """
            SELECT DISTINCT p.user_id, p.user_name, p.email
            FROM phonetry2 p
            LEFT JOIN phones ph ON p.user_id = ph.contact_id
            WHERE p.user_name ILIKE %s OR ph.phone ILIKE %s
            ORDER BY p.user_id
            """,
            ('%' + pattern + '%', '%' + pattern + '%')
        )
        rows = cursor.fetchall()
        print(f"Найдено контактов: {len(rows)}")
        for row in rows:
            print(f"ID: {row[0]} | Имя: {row[1]} | Email: {row[2]}")
    except Exception as e:
        print(f"Ошибка при поиске: {e}")

# Удаление по имени
def delete_by_name(user_name):
    try:
        cursor.execute("DELETE FROM phonetry2 WHERE user_name = %s RETURNING *", (user_name,))
        deleted = cursor.fetchone()
        conn.commit()
        if deleted:
            print(f"Контакт {user_name} удалён.")
        else:
            print(f"Контакт {user_name} не найден.")
    except Exception as e:
        print(f"Ошибка при удалении: {e}")

# Удаление по номеру
def delete_by_phone(numberph):
    try:
        cursor.execute("DELETE FROM phonetry2 WHERE numberph = %s RETURNING *", (numberph,))
        deleted = cursor.fetchone()
        conn.commit()
        if deleted:
            print(f"Контакт с номером {numberph} удалён.")
        else:
            print(f"Контакт с номером {numberph} не найден.")
    except Exception as e:
        print(f"Ошибка при удалении: {e}")


# Вставка сразу нескольких контактов
def insert_multiple_users(data_list):
    for user_name, numberph in data_list:
        if len(numberph) > 10:
            print(f"Неверный номер: {numberph} для {user_name}")
            continue

        cursor.execute("SELECT COUNT(*) FROM phonetry2 WHERE user_name = %s", (user_name,))
        exists = cursor.fetchone()[0]

        if exists:
            cursor.execute("UPDATE phonetry2 SET numberph = %s WHERE user_name = %s", (numberph, user_name))
        else:
            cursor.execute("INSERT INTO phonetry2 (user_name, numberph) VALUES (%s, %s)", (user_name, numberph))

    conn.commit()
    print("Контакты добавлены или обновлены.")

# Показать с пагинацией
def interactive_pagination():
    limit = 3  
    offset = 0

    while True:
        try:
            cursor.execute("""
                SELECT user_id, user_name, email 
                FROM phonetry2 
                ORDER BY user_id 
                LIMIT %s OFFSET %s
            """, (limit, offset))
            
            rows = cursor.fetchall()

            print(f"\n СТРАНИЦА (Контакты с {offset + 1})")
            if not rows:
                print("Здесь больше нет записей")
            else:
                for r in rows:
                    print(f"ID: {r[0]} | 👤 {r[1]} | 📧 {r[2]}")

            print("\n[n] - Next (Вперед) | [p] - Prev (Назад) | [q] - Quit (Выход в меню)")
            cmd = input("Введите команду: ").lower().strip()

            if cmd == 'n':
                if rows:
                    offset += limit
                else:
                    print("Это последняя страница!")
            elif cmd == 'p':
                # Не даем уйти в минус
                offset = max(0, offset - limit)
            elif cmd == 'q':
                break
            else:
                print("Неверная команда!")

        except Exception as e:
            print(f"Ошибка пагинации: {e}")
            break

def import_from_json():
    filename = "contacts.json"
    if not os.path.exists(filename):
        print(f"Файл {filename} не найден! Сначала выполните экспорт (пункт 5).")
        return
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data:
                # Вызываем уже готовую функцию вставки
                insert_or_update_user(item['name'], item['phone'])
        print("Все контакты из JSON загружены в базу.")
    except Exception as e:
        print(f"Ошибка импорта: {e}")

def export_to_json():
    try:
        # Собираем данные: имя, почта и все связанные телефоны
        cursor.execute("""
            SELECT p.user_name, p.email, array_agg(ph.phone) 
            FROM phonetry2 p 
            LEFT JOIN phones ph ON p.user_id = ph.contact_id 
            GROUP BY p.user_id
        """)
        rows = cursor.fetchall()
        data = [{"name": r[0], "email": r[1], "phones": r[2]} for r in rows]
        
        with open("contacts.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print("Данные (включая все номера) сохранены в contacts.json")
    except Exception as e:
        print(f" Ошибка при экспорте: {e}")

def advanced_search():
    print("1 - Фильтр по группе (Family, Work и т.д.)")
    print("2 - Поиск по Email (частичное совпадение)")
    choice = input("Выберите вариант: ")

    try:
        if choice == "1":
            # 1. Сначала выводим список всех групп, чтобы пользователь знал ID
            cursor.execute("SELECT id, name FROM groups")
            groups = cursor.fetchall()
            print("\nДоступные категории:")
            for g in groups:
                print(f"{g[0]} - {g[1]}")
            
            target_group = input("\nВведите ID группы для фильтрации: ")
            
            # 2. Выполняем JOIN, чтобы достать контакты конкретной группы
            query = """
                SELECT p.user_name, p.email, g.name 
                FROM phonetry2 p 
                JOIN groups g ON p.group_id = g.id 
                WHERE g.id = %s
                ORDER BY p.user_name
            """
            cursor.execute(query, (target_group,))

        elif choice == "2":
            email_part = input("Введите часть email (например, 'gmail' или 'mail.ru'): ")
            
            # Используем ILIKE для поиска без учета регистра и % для поиска подстроки
            query = """
                SELECT user_name, email 
                FROM phonetry2 
                WHERE email ILIKE %s 
                ORDER BY user_name
            """
            cursor.execute(query, ('%' + email_part + '%',))
        
        else:
            print("Неверный выбор")
            return

        # Вывод результатов
        results = cursor.fetchall()
        print(f"\nНайдено записей: {len(results)}")
        print("-" * 30)
        for row in results:
            if choice == "1":
                print(f"{row[0]} | {row[1]} | Группа: {row[2]}")
            else:
                print(f"{row[0]} | {row[1]}")
        print("-" * 30)

    except Exception as e:
        print(f"Ошибка поиска: {e}")

def show_sorted_contacts():
    print("1 - По имени (А-Я)")
    print("2 - По дню рождения")
    print("3 - По дате добавления (сначала новые)")
    choice = input("Выберите вариант сортировки: ")

    # Словарь для сопоставления выбора и колонок в БД
    sort_options = {
        "1": "user_name ASC",
        "2": "birthday ASC",
        "3": "user_id DESC"
    }

    column = sort_options.get(choice, "user_name ASC")

    try:
        # Выбираем данные со связями, чтобы было красиво
        query = f"""
            SELECT p.user_name, p.birthday, p.email, g.name
            FROM phonetry2 p
            LEFT JOIN groups g ON p.group_id = g.id
            ORDER BY {column}
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        print(f"\n{'Имя':<15} | {'День рождения':<12} | {'Группа':<10}")
        print("-" * 45)
        for r in rows:
            bday = r[1].strftime('%d.%m.%Y') if r[1] else "Не указан"
            print(f"{r[0]:<15} | {bday:<12} | {r[3] if r[3] else '-':<10}")
            
    except Exception as e:
        print(f"Ошибка при сортировке: {e}")

def call_move_to_group():
    name = input("Имя контакта: ")
    group = input("Название новой группы (создастся, если нет): ")
    try:
        cursor.execute("CALL move_to_group(%s, %s)", (name, group))
        conn.commit()
        print(f"Контакт {name} переведен в группу {group}")
    except Exception as e:
        print(f"Ошибка: {e}")

def call_global_search():
    query = input("Введите что искать (имя, почту или номер): ")
    try:
        # Функции в Postgres вызываются через SELECT
        cursor.execute("SELECT * FROM search_contacts_all(%s)", (query,))
        rows = cursor.fetchall()
        print(f"\nНайдено результатов: {len(rows)}")
        for r in rows:
            print(f" {r[0]} |{r[1]} |{r[2]}")
    except Exception as e:
        print(f"Ошибка поиска: {e}")

# Главное меню
if __name__ == '__main__':
    try:
        operation = input(
            "Выберите операцию:\n"
            "1 - Добавить или обновить контакт\n"
            "2 - Искать по шаблону\n"
            "3 - Удалить по имени\n"
            "4 - Удалить по номеру\n"
            "5 - Импортировать в json\n"
            "6 - Экспортировать в json\n"
            "7 - Показать все контакты\n"
            "8 - Показать контакты с пагинацией\n"
            "10 - расширенный поиск\n"
            "11 - Сортированный список\n"
            "13 - Добавить телефон существующему контакту (через процедуру)\n"
            "14 - Перевести контакт в другую группу (через процедуру)\n"
            "15 - Глобальный поиск по всем полям (через функцию)\n"

            "Ваш выбор: "
        )

        if operation == "1":
            add_contact_with_details()

        elif operation == "2":
            pattern = input("Введите часть имени или номера: ")
            search_by_pattern(pattern)

        elif operation == "3":
            name = input("Имя для удаления: ")
            delete_by_name(name)

        elif operation == "4":
            phone = input("Номер для удаления: ")
            delete_by_phone(phone)

        elif operation == "5":
            import_from_json()

        elif operation == "6":
            export_to_json()

        elif operation == "7":
            show_all_detailed()

        elif operation == "8":
            interactive_pagination()

        elif operation == "10":
            advanced_search()
        
        elif operation == "11":
            show_sorted_contacts()
        
        elif operation == "13":
            name = input("Имя контакта: ")
            phone = input("Номер: ")
            ptype = input("Тип (home/work/mobile): ")
            cursor.execute("CALL add_phone_to_contact(%s, %s, %s)", (name, phone, ptype))
            conn.commit()
            print("Телефон добавлен")

        elif operation == "14":
            call_move_to_group()

        elif operation == "15":
            call_global_search()
        

        else:
            print("Неверный ввод!")

    except Exception as e:
        print(f"Ошибка при выполнении операции: {e}")

    finally:
        cursor.close()
        conn.close()