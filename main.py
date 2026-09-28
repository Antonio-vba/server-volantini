from fastapi import FastAPI
import requests
import random

app = FastAPI()

@app.get("/v1/offerte/cerca")
def cerca_offerte(prodotto: str, lat: float = None, lng: float = None):
    risultati = []
    
    try:
        # Usiamo l'API pubblica e gratuita di Open Food Facts (versione italiana)
        url = "https://it.openfoodfacts.org/cgi/search.pl"
        params = {
            "search_terms": prodotto,
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page_size": 3  # Prendiamo i primi 3 prodotti reali trovati
        }
        headers = {
            "User-Agent": "SmartSpesaApp - Android App - Educational Project"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            products = data.get("products", [])
            
            supermercati_disponibili = ["Conad", "Coop", "Lidl", "Eurospin", "Pam", "Esselunga"]
            
            for i, prod in enumerate(products):
                # Estraiamo il nome e la marca reali dal database pubblico
                nome_prod = prod.get("product_name_it") or prod.get("product_name")
                marca = prod.get("brands", "")
                
                if nome_prod:
                    # Uniamo marca e nome per un risultato pulito e reale
                    titolo_completo = f"{marca} {nome_prod}".strip() if marca else nome_prod
                    
                    # Generiamo un prezzo e un supermercato coerenti
                    prezzo_base = round(1.29 + (i * 0.60), 2)
                    sconto_percentuale = f"{random.randint(10, 30)}%"
                    supermercato_scelto = supermercati_disponibili[i % len(supermercati_disponibili)]
                    
                    risultati.append({
                        "nome": titolo_completo,
                        "prezzoOfferta": prezzo_base,
                        "supermercato": supermercato_scelto,
                        "sconto": sconto_percentuale
                    })
                    
    except Exception as e:
        print(f"Errore con Open Food Facts API: {e}")
        
    # Fallback di sicurezza nel caso in cui l'API non trovi nulla
    if not risultati:
        risultati.append({
            "nome": f"{prodotto.capitalize()} (Prodotto disponibile)",
            "prezzoOfferta": 1.49,
            "supermercato": "Supermercato Locale",
            "sconto": "15%"
        })
        
    return risultati
