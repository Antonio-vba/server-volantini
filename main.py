from fastapi import FastAPI
from pydantic import BaseModel
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

app = FastAPI()

# Funzione per connettersi a Google Sheets in modo sicuro
def get_sheets_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Legge le credenziali dalla variabile d'ambiente impostata su Render
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if creds_json:
        creds_dict = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        return client
    return None

# Modello dei dati inviato dall'app Android
class ProdottoInserito(BaseModel):
    nome: str
    prezzoPieno: float
    prezzoOfferta: float
    supermercato: str
    sconto: str = "Offerta"

@app.post("/v1/offerte/aggiungi")
def aggiungi_prodotto(prodotto: ProdottoInserito):
    try:
        client = get_sheets_client()
        if not client:
            return {"status": "errore", "messaggio": "Credenziali Google non configurate sul server."}
        
        # Apre il foglio Google chiamato "SmartSpesaDB"
        sheet = client.open("SmartSpesaDB").sheet1
        
        # Aggiunge una nuova riga con i dati inviati dall'app
        sheet.append_row([
            prodotto.nome,
            prodotto.prezzoPieno,
            prodotto.prezzoOfferta,
            prodotto.supermercato,
            prodotto.sconto
        ])
        
        return {"status": "successo", "messaggio": "Prodotto salvato nel Google Sheet!"}
    except Exception as e:
        return {"status": "errore", "messaggio": str(e)}

@app.get("/v1/offerte/cerca")
def cerca_offerte(prodotto: str, lat: float = None, lng: float = None):
    risultati = []
    termine = prodotto.lower().strip()
    
    try:
        client = get_sheets_client()
        if client:
            sheet = client.open("SmartSpesaDB").sheet1
            # Legge tutte le righe del foglio (saltando l'intestazione)
            righe = sheet.get_all_records()
            
            for riga in righe:
                nome_foglio = str(riga.get("nome", "")).lower()
                supermercato_foglio = str(riga.get("supermercato", "")).lower()
                
                # Se il termine cercato corrisponde al nome o al supermercato
                if termine in nome_foglio or termine in supermercato_foglio:
                    risultati.append({
                        "nome": riga.get("nome"),
                        "prezzoPieno": float(riga.get("prezzoPieno", 0)),
                        "prezzoOfferta": float(riga.get("prezzoOfferta", 0)),
                        "supermercato": riga.get("supermercato"),
                        "sconto": str(riga.get("sconto", "Offerta"))
                    })
    except Exception as e:
        print(f"Errore lettura Google Sheet: {e}")
        
    # Se il foglio non ha trovato nulla, restituisce un fallback descrittivo
    if not risultati:
        risultati.append({
            "nome": f"{prodotto.capitalize()} (Nessun volantino trovato nel database)",
            "prezzoPieno": 0.0,
            "prezzoOfferta": 0.0,
            "supermercato": "N/D",
            "sconto": "N/D"
        })
        
    return risultati
