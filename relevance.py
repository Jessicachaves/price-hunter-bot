import re
import unicodedata
from typing import List, Tuple

STOPWORDS = {
    "de", "da", "do", "das", "dos", "para", "pra", "pro", "com", "sem",
    "e", "o", "a", "os", "as", "em", "no", "na", "nos", "nas", "um", "uma", "uns", "umas"
}

SYNONYMS = {
    "controle": ["controle", "joystick", "dualsense", "dualshock", "gamepad", "controlador", "manete"],
    "joystick": ["joystick", "controle", "gamepad", "dualsense"],
    "dualsense": ["dualsense", "controle ps5", "ps5"],
    "cabo": ["cabo", "cable", "extensor"],
    "fone": ["fone", "headphone", "headset", "auricular", "earbuds"],
    "celular": ["celular", "smartphone", "telefone"],
    "notebook": ["notebook", "laptop"],
}

# Palavras que indicam o objeto principal vendido quando iniciam o título
PREFIX_NOUNS = {
    "kit", "grip", "grips", "capa", "capinha", "case", "suporte", "base", "dock",
    "carregador", "bateria", "pelicula", "skin", "adesivo", "analogico", "analogicos",
    "extensor", "extensores", "protetor", "reparo", "peca", "pecas", "cabo", "cabos",
    "adaptador", "adaptadores"
}

def normalize(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]", " ", text.lower()).strip()

def get_query_tokens(query: str) -> List[str]:
    norm = normalize(query)
    tokens = [t for t in norm.split() if t not in STOPWORDS and len(t) >= 2]
    return tokens

def match_token(title_norm: str, token: str) -> bool:
    syns = SYNONYMS.get(token, [token])
    for s in syns:
        if re.search(rf"\b{re.escape(s)}", title_norm):
            return True
    return False

def is_unrelated_prefix(title_norm: str, query_norm: str) -> bool:
    """
    Verifica se o título começa com um substantivo secundário que o usuário NÃO pesquisou.
    Ex: usuário buscou "controle ps5" e o anúncio começa com "Kit 8 Grips..." ou "Suporte...".
    Se o usuário buscou "cabo para controle", o prefixo "cabo" É aceito normalmente!
    """
    query_words = set(query_norm.split())
    first_words = [w for w in title_norm.split()[:3] if w not in STOPWORDS]
    if first_words:
        first_word = first_words[0]
        if first_word in PREFIX_NOUNS and first_word not in query_words:
            return True
    return False

def filter_relevant(offers: list, query: str) -> Tuple[list, int]:
    """
    Filtro inteligente baseado nas palavras digitadas pelo usuário:
    - Nenhuma palavra é permanentemente bloqueada.
    - O que o usuário digitar na busca SEMPRE será aceito.
    - Se a busca for por "controle", descarta itens que começam com "Grips", "Suporte", etc.
    - Se a busca for por "cabo para controle", mantém todos os cabos!
    """
    if not offers:
        return [], 0

    tokens = get_query_tokens(query)
    query_norm = normalize(query)
    if not tokens:
        return offers, 0

    kept = []
    for o in offers:
        title_norm = normalize(o.title)
        
        # 1. Deve conter as palavras da pesquisa (ou sinônimos)
        matches = sum(1 for t in tokens if match_token(title_norm, t))
        
        if len(tokens) == 1:
            is_match = matches >= 1
        elif len(tokens) == 2:
            is_match = matches >= 2
        else:
            is_match = matches >= max(2, int(len(tokens) * 0.6))
            
        if not is_match:
            continue
            
        # 2. Não deve ser um acessório cujo sujeito inicial o usuário não pediu
        if is_unrelated_prefix(title_norm, query_norm):
            continue
            
        kept.append(o)

    # Fallback de segurança: se filtrou tudo, relaxa
    if len(kept) < 2 and len(offers) >= 2:
        kept = [o for o in offers if sum(1 for t in tokens if match_token(normalize(o.title), t)) >= 1]

    return kept, len(offers) - len(kept)
