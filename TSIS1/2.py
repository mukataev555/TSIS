import psycopg2
from psycopg2 import sql
# -*- coding: utf-8 -*-

conn = psycopg2.connect(
    dbname="phonebook",  
    user="postgres",   
    password="alibek08",  
    host="localhost",          
)

cursor = conn.cursor()

def from_csv_to_db(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        next(file)  
        for line in file:
            user_name, numberph = line.strip().split(',')
            insert_query = """
            INSERT INTO phonetry2 (user_name, numberph) 
            VALUES (%s, %s);
            """
            cursor.execute(insert_query, (user_name, int(numberph)))
    conn.commit()
    print("Данные из CSV файла успешно импортированы в базу данных.")

def create_column():
    create_column_query = """
    ALTER TABLE phonetry2
    ADD COLUMN IF NOT EXISTS numbe INT DEFAULT 0;
    """
    cursor.execute(create_column_query)
    conn.commit()
    print("Столбец 'numberph' успешно добавлен в таблицу 'phonetry2'.")

def delate_column():
    delete_column_query = """
    ALTER TABLE phonetry2
    DROP COLUMN IF EXISTS numbe;
    """
    cursor.execute(delete_column_query)
    conn.commit()
    print("Столбец 'numberph' успешно удалён из таблицы 'phonetry2'.")



def insert_user(user_name, numberph):
    insert_query = """
    INSERT INTO phonetry2 (user_name, numberph) 
    VALUES (%s, %s) RETURNING user_id, user_name, numberph;
    """
    cursor.execute(insert_query, (user_name, numberph))
    conn.commit()
    user_data = cursor.fetchone()
    print(f"Пользователь добавлен: ID = {user_data[0]}, Имя = {user_data[1]}, Number = {user_data[2]}")
    return user_data[0]  # Возвращаем ID нового пользователя

def update(num, user_name, numberph):
    if num == 1:
         update_query = """
            UPDATE phonetry2
            SET numberph = %s
            WHERE user_name = %s
            RETURNING user_id, user_name, numberph;
            """
    elif num == 2:
        update_query = """
            UPDATE phonetry2
            SET user_name = %s
            WHERE numberph = %s
            RETURNING user_id, user_name, numberph;
            """

    cursor.execute(update_query, ( numberph, user_name))  
    conn.commit()
    user_data = cursor.fetchone()

    if user_data:
        print(f"Данные обновлены: ID = {user_data[0]}, Имя = {user_data[1]}, Новые баллы = {user_data[2]}")
    else:
        if num == 1:
            print("Пользователь не найден.")
        elif num == 2:
            print("Номер не найден.")

def delete_user(user_name):   
    delete_query = """
    DELETE FROM phonetry2
    WHERE user_name = %s
    RETURNING user_id, user_name;
    """
    cursor.execute(delete_query, (user_name,))
    conn.commit()

    user_data = cursor.fetchone()

    if user_data:
        print(f"Пользователь удален: ID = {user_data[0]}, Имя = {user_data[1]}")
    else:
        print("Пользователь не найден.")

def get_users_sorted_by_number():
    select_query = "SELECT user_id, user_name, numberph FROM phonetry2 ORDER BY numberph DESC;"
    cursor.execute(select_query)

    rows = cursor.fetchall()

    print("Пользователи, отсортированные по баллам (от максимального):")
    for row in rows:
        print(f"ID: {row[0]}, Имя: {row[1]}, Баллы: {row[2]}")

if __name__ == '__main__':
    oper = input("Введите операцию (1 - добавить, 2 - удалить, 3 - обновить, 4 - получить всех), 5 - create column, 6 delate c: ")
    if oper == '1':
        b = input("Введите 1 - добавить из CSV, 2 - добавить вручную: ")
        if b == '1':
            file_path = input("Введите путь к CSV файлу: ")
            from_csv_to_db(file_path)
        elif b == '2':
            user_name = input("Введите имя: ")
            numberph = int(input("Введите номер телефона: "))
            insert_user(user_name, numberph)
    elif oper == '2':
        user_name = input("Введите имя для удаления: ")
        delete_user(user_name)
    elif oper == '3':
        num = int(input("Введите 1 - обновить номер, 2 - обновить имя: "))
        if num == 1:
            user_name = input("Введите имя: ")
            numberph = int(input("Введите новый номер телефона: "))
            update(num, user_name, numberph)
        elif num == 2:
            numberph = int(input("Введите номер телефона: "))
            user_name = input("Введите новое имя: ")
            update(num, user_name, numberph)
    elif oper == '4':
        get_users_sorted_by_number()
    elif oper == '5':
        create_column()
    elif oper == '6':
        delate_column()
    else:
        print("Неверная операция.")
    