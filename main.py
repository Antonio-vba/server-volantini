from fastapi import FastAPI
import requests
import random

app = FastAPI()

@app.get("/v1/offerte/cerca")
def cerca_offerte(prodotto: str, lat: float = None, lng: float = None):
    risultati = []
    termine_ricerca = prodotto.lower().strip()
    
    try:
        # Usiamo l'API pubblica di Open Food Facts
        url = "https://it.openfoodfacts.org/cgi/search.pl"
        params = {
            "search_terms": prodotto,
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page_size": 3
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
                nome_prod = prod.get("product_name_it") or prod.get("product_name")
                marca = prod.get("brands", "")
                
                if nome_prod:
                    titolo_completo = f"{marca} {nome_prod}".strip() if marca else nome_prod
                    prezzo_base = round(1.29 + (i * 0.70), 2)
                    sconto_percentuale = f"{random.randint(15, 35)}%"
                    supermercato_scelto = supermercati_disponibili[i % len(supermercati_disponibili)]
                    
                    risultati.append({
                        "nome": titolo_completo,
                        "prezzoOfferta": prezzo_base,
                        "supermercato": supermercato_scelto,
                        "sconto": sconto_percentuale
                    })
                    
    except Exception as e:
        print(f"Errore con Open Food Facts: {e}")
        
    # Se Open Food Facts non restituisce prodotti per quella specifica ricerca,
    # generiamo un'offerta realistica basata esattamente su quello che ha digitato l'utente
    if not risultati:
        prezzi_finti = [1.49, 1.99, 2.49, 0.99]
        supermercati_finti = ["Lidl", "Conad", "Coop", "Eurospin"]
        
        risultati.append({
            "nome": f"{prodotto.capitalize()} - Offerta Volantino",
            "prezzoOfferta": random.choice(prezzi_finti),
            "supermercato": random.choice(supermercati_finti),
            "sconto": f"{random.randint(10, 30)}%"
        })
        
    return risultati
