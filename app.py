import os
import sys
import webbrowser
from dataclasses import asdict
from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, Dict, Any

from engine import engine
import database

app = FastAPI(title="Radar de Preços", description="Comparador Inteligente de Preços Multilojas")
templates = Jinja2Templates(directory="templates")

class AlertRequest(BaseModel):
    query: str
    target_price: float
    notify_channel: Optional[str] = "web"

class FavoriteRequest(BaseModel):
    title: str
    price: float
    store: str
    link: str
    image_url: Optional[str] = ""

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    try:
        return templates.TemplateResponse(request=request, name="index.html")
    except Exception:
        with open("templates/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())

@app.get("/api/search")
def api_search(q: str = Query(..., min_length=1)):
    try:
        raw_results = engine.search_all_sync(q)
        
        # Converte dataclasses para dicionários JSON-friendly
        results = {
            "query": raw_results["query"],
            "total_found": raw_results["total_found"],
            "cheapest": asdict(raw_results["cheapest"]) if raw_results["cheapest"] else None,
            "most_expensive": asdict(raw_results["most_expensive"]) if raw_results["most_expensive"] else None,
            "average_price": raw_results["average_price"],
            "average_price_formatted": raw_results["average_price_formatted"],
            "max_savings": raw_results["max_savings"],
            "max_savings_formatted": raw_results["max_savings_formatted"],
            "savings_vs_avg": raw_results["savings_vs_avg"],
            "savings_vs_avg_formatted": raw_results["savings_vs_avg_formatted"],
            "offers": [asdict(o) for o in raw_results["offers"]],
            "source_counts": raw_results["source_counts"],
            "search_time_sec": raw_results["search_time_sec"]
        }

        # Salva no histórico do banco SQLite
        database.save_search(q, results.get("cheapest"), results.get("total_found", 0))
        return JSONResponse(content=results)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/alerts")
async def get_alerts():
    return JSONResponse(content=database.get_alerts())

@app.post("/api/alerts")
async def create_alert(item: AlertRequest):
    database.add_price_alert(item.query, item.target_price, item.notify_channel)
    return JSONResponse(content={"success": True, "message": "Alerta cadastrado com sucesso!"})

@app.get("/api/favorites")
async def get_favorites():
    return JSONResponse(content=database.get_favorites())

@app.post("/api/favorites")
async def toggle_favorite(item: FavoriteRequest):
    added = database.toggle_favorite(item.dict())
    return JSONResponse(content={"success": True, "added": added})

@app.get("/api/history")
async def get_history():
    return JSONResponse(content=database.get_recent_searches())

@app.on_event("startup")
def startup_event():
    # Inicializa o Bot do Telegram em segundo plano se o token estiver configurado
    import threading
    try:
        from telegram_bot import bot
        if bot and getattr(bot, "token", None) and ":" in str(bot.token) and "COLOQUE" not in str(bot.token):
            def run_bot():
                try:
                    bot.infinity_polling(timeout=20, long_polling_timeout=20)
                except Exception as b_err:
                    print(f"[ERROR] Erro no bot do Telegram: {b_err}")
            threading.Thread(target=run_bot, daemon=True).start()
            print("[INFO] Bot do Telegram iniciado em segundo plano")
    except Exception as e:
        print(f"[INFO] Bot do Telegram nao iniciado: {e}")

if __name__ == "__main__":
    import uvicorn
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8080))
    url = f"http://localhost:{port}"
    print(f"\n=======================================================")
    print(f"Radar de Precos - Servidor ativo")
    print(f"Acesse: {url}")
    print(f"=======================================================\n")
    uvicorn.run("app:app", host=host, port=port, reload=False)

