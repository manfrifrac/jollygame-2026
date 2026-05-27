import sqlite3
conn = sqlite3.connect('fluidra_catalog.db')
cursor = conn.cursor()
try:
    cursor.execute('ALTER TABLE products ADD COLUMN diagram_url TEXT')
    print('✅ Colonna diagram_url aggiunta.')
except sqlite3.OperationalError:
    print('⚠️ Colonna già presente.')
conn.commit()
conn.close()
