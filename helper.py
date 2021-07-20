from os import getenv

import mysql.connector

db_connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password=getenv("MySQLpassword"),
    database="mobinfo"
)

db = db_connection.cursor()

db_connection.commit()

def get_brand_details(brand_name):
    db.execute(f"""
    SELECT name, logo_url, description FROM brand
    WHERE name = %s;
    """, (brand_name, ))
    return db.fetchone()
