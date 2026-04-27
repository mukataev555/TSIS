import psycopg2
from psycopg2 import sql
# -*- coding: utf-8 -*-

conn = psycopg2.connect(
    dbname='phonebook',
    user='postgres',
    password='alibek08',
    host='localhost'
)
cursor = conn.cursor()


create_table_query = """
CREATE TABLE IF NOT EXISTS phonetry2 (
    user_id SERIAL PRIMARY KEY,
    user_name VARCHAR(100) NOT NULL,
    numberph VARCHAR(100)
);
"""
cursor.execute(create_table_query)


conn.commit()

cursor.close()
conn.close()

print('users')