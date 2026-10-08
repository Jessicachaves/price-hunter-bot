import sqlite3
import datetime
from typing import List, Dict, Any, Optional

DB_PATH = "price_hunter.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabela de buscas recentes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            cheapest_title TEXT,
            cheapest_price REAL,
            cheapest_store TEXT,
            cheapest_link TEXT,
            total_offers INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de alertas de preço desejado
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            target_price REAL NOT NULL,
            user_identifier TEXT DEFAULT 'local_user',
            notify_channel TEXT DEFAULT 'web',
            is_active INTEGER DEFAULT 1,
            last_checked TIMESTAMP,
            last_price REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de favoritos / watchlist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            price REAL NOT NULL,
            store TEXT NOT NULL,
            link TEXT NOT NULL,
            image_url TEXT,
            query_used TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def save_search(query: str, cheapest_offer: Optional[Dict], total_offers: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO search_history (query, cheapest_title, cheapest_price, cheapest_store, cheapest_link, total_offers)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        query,
        cheapest_offer.get('title') if cheapest_offer else None,
        cheapest_offer.get('price') if cheapest_offer else None,
        cheapest_offer.get('store') if cheapest_offer else None,
        cheapest_offer.get('link') if cheapest_offer else None,
        total_offers
    ))
    conn.commit()
    conn.close()

def get_recent_searches(limit: int = 10) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM search_history ORDER BY id DESC LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_price_alert(query: str, target_price: float, notify_channel: str = "web", user_identifier: str = "local_user"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO price_alerts (query, target_price, notify_channel, user_identifier)
        VALUES (?, ?, ?, ?)
    ''', (query, target_price, notify_channel, user_identifier))
    conn.commit()
    conn.close()

def get_alerts() -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM price_alerts ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def toggle_favorite(item: Dict[str, Any]) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Check if already in favorites
    cursor.execute('SELECT id FROM favorites WHERE link = ?', (item.get('link'),))
    existing = cursor.fetchone()
    if existing:
        cursor.execute('DELETE FROM favorites WHERE id = ?', (existing[0],))
        added = False
    else:
        cursor.execute('''
            INSERT INTO favorites (title, price, store, link, image_url, query_used)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            item.get('title'),
            item.get('price'),
            item.get('store'),
            item.get('link'),
            item.get('image_url'),
            item.get('query_used', '')
        ))
        added = True
    conn.commit()
    conn.close()
    return added

def get_favorites() -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM favorites ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

init_db()

