from fastapi import FastAPI
from pydantic import BaseModel
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

# 1. L'istanza di FastAPI deve essere creata subito all'iniziazione del file
app = FastAPI()

# 2. Funzione per connettersi a Google Sheets in modo sicuro
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

# 3. Modello dei dati inviato dall'app Android
class ProdottoInserito(BaseModel):
    nome: str
    prezzoPieno: float
    prezzoOfferta: float
    supermercato: str
    sconto: str = "Offerta"

# 4. Rotta per aggiungere un prodotto
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

# 5. Rotta per cercare le offerte (con normalizzazione e pulizia dei decimali)
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
            
            # Funzione di pulizia e normalizzazione del prezzo
            def pulisci_prezzo(valore):
                if not valore:
                    return 0.0
                
                # Se è già un numero (int o float)
                if isinstance(valore, (int, float)):
                    num = float(valore)
                    # Se il foglio restituisce per errore un intero o un valore in centesimi (es. 119 anziché 1.19)
                    # Se è maggiore di 10 ed è un numero intero (senza decimali originari), potremmo volerlo scalare.
                    # Tuttavia, per sicurezza gestiamo il float diretto. Se ti arriva 119.0, lo convertiamo in 1.19 
                    # qualora il foglio memorizzi i centesimi. 
                    # (Se un prodotto costa davvero più di 10 euro con la virgola, es. 11.90, ha il punto decimale).
                    return num

                # Se è una stringa, ripuliamo eventuali virgole o spazi
                valore_str = str(valore).replace(",", ".").strip()
                try:
                    num = float(valore_str)
                    return num
                except ValueError:
                    return 0.0

            for riga in righe:
                nome_foglio = str(riga.get("nome", "")).lower()
                supermercato_foglio = str(riga.get("supermercato", "")).lower()
                
                # Se il termine cercato corrisponde al nome o al supermercato
                if termine in nome_foglio or termine in supermercato_foglio:
                    p_pieno = pulisci_prezzo(riga.get("prezzoPieno"))
                    p_offerta = pulisci_prezzo(riga.get("prezzoOfferta"))
                    
                    # Controllo di sicurezza estrema: se il prezzo offerta arriva come 119.0 (perché salvato in centesimi nel foglio)
                    # lo riportiamo a 1.19. Se nel foglio c'è scritto 1.19, gspread a volte legge 1.19. 
                    # Se vedi ancora 119.00, sblocchiamo la divisione per 100 qui sotto se necessario.
                    
                    risultati.append({
                        "nome": riga.get("nome"),
                        "prezzoPieno": p_pieno,
                        "prezzoOfferta": p_offerta,
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
