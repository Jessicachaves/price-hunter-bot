import urllib.parse
from typing import List, Optional
from curl_cffi import requests
from models import ProductOffer

def format_brl(val: float) -> str:
    return f"R$ {val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def search_kabum(query: str, limit: int = 15) -> List[ProductOffer]:
    results = []
    encoded_query = urllib.parse.quote(query)
    url = f"https://servicespub.prod.api.aws.grupokabum.com.br/catalog/v2/products?query={encoded_query}&page_number=1&page_size={limit}&facet_filters=&sort=most_searched"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Origin': 'https://www.kabum.com.br',
        'Referer': 'https://www.kabum.com.br/'
    }
    
    try:
        resp = requests.get(url, headers=headers, impersonate="chrome124", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get('data', [])
            for item in items:
                attrs = item.get('attributes', {})
                title = attrs.get('title')
                if not title:
                    continue
                
                # Check price (with discount if available)
                price_val = attrs.get('price_with_discount') or attrs.get('price')
                if not price_val or price_val <= 0:
                    continue
                
                old_price = attrs.get('old_price') or attrs.get('price')
                discount = None
                if old_price and old_price > price_val:
                    discount = int(((old_price - price_val) / old_price) * 100)
                
                # Friendly URL slug
                slug = attrs.get('slug') or item.get('id')
                link = f"https://www.kabum.com.br/produto/{slug}"
                
                # Image safely
                img_url = ""
                photos = attrs.get('photos')
                if isinstance(photos, list) and len(photos) > 0 and isinstance(photos[0], dict):
                    img_url = photos[0].get('small') or photos[0].get('original') or ""
                elif isinstance(attrs.get('image'), str):
                    img_url = attrs.get('image')
                
                rating = str(attrs.get('rating', '')) if attrs.get('rating') else None
                
                results.append(ProductOffer(
                    title=title,
                    price=float(price_val),
                    price_formatted=format_brl(float(price_val)),
                    store="KaBuM!",
                    link=link,
                    source="KaBuM!",
                    image_url=img_url,
                    rating=rating,
                    original_price=float(old_price) if old_price else None,
                    discount_pct=discount
                ))
    except Exception as e:
        print(f"[Scraper KaBuM] Error: {e}")
        
    return results

if __name__ == '__main__':
    res = search_kabum("controle ps5 dualsense")
    print(f"KaBuM results: {len(res)}")
    for r in res[:3]:
        print(f"  • {r.title} -> {r.price_formatted} ({r.link})")

