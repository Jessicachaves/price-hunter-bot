import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import urllib.parse
from typing import List, Optional
from curl_cffi import requests
from bs4 import BeautifulSoup
from models import ProductOffer

def parse_price(price_str: str) -> Optional[float]:
    if not price_str:
        return None
    cleaned = re.sub(r'[^\d,.]', '', str(price_str))
    if ',' in cleaned and '.' in cleaned:
        cleaned = cleaned.replace('.', '').replace(',', '.')
    elif ',' in cleaned:
        cleaned = cleaned.replace(',', '.')
    try:
        return float(cleaned)
    except ValueError:
        return None

def format_brl(val: float) -> str:
    return f"R$ {val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def search_bing_shopping(query: str, limit: int = 30) -> List[ProductOffer]:
    results = []
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.bing.com/shop?q={encoded_query}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8',
    }
    
    try:
        resp = requests.get(url, headers=headers, impersonate="chrome124", timeout=12)
        if resp.status_code != 200:
            return results
            
        soup = BeautifulSoup(resp.text, 'lxml')
        cards = soup.select('li.br-item, div.br-card, div[class*="br-item"], .br-standardCard')
        
        seen_titles = set()
        for card in cards:
            if len(results) >= limit:
                break
                
            text = card.get_text(" ", strip=True)
            if 'R$' not in text:
                continue
                
            # Title
            t_el = card.select_one('.br-title, a[class*="title"], h3, .br-sellerFocusTitle')
            title = t_el.get_text(strip=True) if t_el else ""
            if not title or len(title) < 5:
                continue
                
            # Clean duplicate repetitive words in Bing titles if any
            if len(title) > 30 and title[:15] == title[15:30]:
                title = title[:len(title)//2]
                
            # Price
            price_match = re.search(r'R\$\s*([\d.]+,\d{2}|\d+)', text)
            if not price_match:
                continue
            price_val = parse_price(price_match.group(0))
            if not price_val or price_val <= 0:
                continue
                
            # Seller / Store
            s_el = card.select_one('.br-seller, .seller, .br-sellers, span[class*="seller"], .br-sellerName')
            seller = s_el.get_text(strip=True) if s_el else ""
            if not seller or seller.lower() == 'anúncio':
                seller_match = re.search(r'(Mercado Livre|Amazon BR|Amazon|KaBuM!|KaBuM|Shopee|Magalu|Magazine Luiza|Casas Bahia|Ponto|Carrefour|Terabyte|Pichau|AliExpress)', text, re.IGNORECASE)
                seller = seller_match.group(0) if seller_match else "Loja Online"
                
            # Link
            link = ""
            for a in card.select('a[href]'):
                href = a.get('href')
                if href and not href.startswith('javascript'):
                    link = f"https://www.bing.com{href}" if href.startswith('/') else href
                    break
                    
            # Image
            img_el = card.select_one('img')
            img = img_el.get('src') or img_el.get('data-src') if img_el else ""
            
            key = (title[:30].lower(), round(price_val, 0))
            if key in seen_titles:
                continue
            seen_titles.add(key)
            
            results.append(ProductOffer(
                title=title,
                price=price_val,
                price_formatted=format_brl(price_val),
                store=seller,
                link=link,
                source="Shopping MultiLojas",
                image_url=img
            ))
    except Exception as e:
        print(f"[Scraper Bing Shop] Error: {e}")
        
    return results

if __name__ == '__main__':
    res = search_bing_shopping("controle ps5 dualsense")
    print(f"Shopping MultiLojas total: {len(res)}")
    for r in res[:5]:
        print(f"  • [{r.store}] {r.title[:40]} -> {r.price_formatted}")

