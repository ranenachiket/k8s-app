import psycopg2

conn = psycopg2.connect(
    host="192.168.87.33",   # Pi's IP
    database="orders",
    user="admin",
    password="admin"
)
cur = conn.cursor()
cur.execute("SELECT version();")
print(cur.fetchone())
conn.close()