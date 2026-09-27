from fastapi import FastAPI
import uvicorn

app = FastAPI()

database_offerte = [
    {"nome": "Ringo Pavesi 330g", "prezzoOfferta": 1.99, "supermercato": "Lidl", "sconto": "20%"},
    {"nome": "Nutella 750g", "prezzoOfferta": 4.50, "supermercato": "Conad", "sconto": "15%"},
]

@app.get("/v1/offerte/cerca")
def cerca_offerte(prodotto: str, lat: float = None, lng: float = None):
    risultati = []
    for offerta in database_offerte:
        if prodotto.lower() in offerta["nome"].lower():
            risultati.append(offerta)
    return risultati
