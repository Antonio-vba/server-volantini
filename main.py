from fastapi import FastAPI
from pydantic import BaseModel
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

app = FastAPI()

def get_sheets_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if creds_json:
        creds_dict = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        return client
    return None

# Modello dei dati per le scadenze
class ScadenzaServer(BaseModel):
    id: int
    nome: str
    importo: float
    dataScadenza: str
    categoria: str
    pagata: bool = False

# 1. Rotta per SCARICARE tutte le scadenze dal Google Sheet
@app.get("/v1/scadenze")
def ottieni_scadenze():
    try:
        client = get_sheets_client()
        if not client:
            return []
        
        sheet = client.open("SmartSpesaDB").sheet1
        righe = sheet.get_all_records()
        
        scadenze = []
        for i, riga in enumerate(righe):
            scadenze.append({
                "id": i + 1,
                "nome": riga.get("nome", ""),
                "importo": float(str(riga.get("importo", 0)).replace(",", ".") or 0),
                "dataScadenza": str(riga.get("dataScadenza", "")),
                "categoria": str(riga.get("categoria", "Utenze")),
                "pagata": bool(riga.get("pagata", False))
            })
        return scadenze
    except Exception as e:
        print(f"Errore lettura scadenze: {e}")
        return []

# 2. Rotta per AGGIUNGERE una nuova scadenza nel Google Sheet
@app.post("/v1/scadenze/aggiungi")
def aggiungi_scadenza(scadenza: ScadenzaServer):
    try:
        client = get_sheets_client()
        if not client:
            return {"status": "errore", "messaggio": "Credenziali Google non configurate."}
        
        sheet = client.open("SmartSpesaDB").sheet1
        
        sheet.append_row([
            scadenza.nome,
            scadenza.importo,
            scadenza.dataScadenza,
            scadenza.categoria,
            scadenza.pagata
        ])
        
        return {"status": "successo", "messaggio": "Scadenza salvata nel foglio!"}
    except Exception as e:
        return {"status": "errore", "messaggio": str(e)}

# 3. Rotta per SEGNARE una bolletta come PAGATA nel Google Sheet
@app.put("/v1/scadenze/{scadenza_id}/paga")
def segna_pagata(scadenza_id: int):
    try:
        client = get_sheets_client()
        if not client:
            return {"status": "errore", "messaggio": "Credenziali Google non configurate."}
        
        sheet = client.open("SmartSpesaDB").sheet1
        
        # scadenza_id corrisponde all'indice + 1. Nel foglio Google, 
        # la riga 1 è l'intestazione, quindi la riga dati è scadenza_id + 1
        riga_foglio = scadenza_id + 1
        
        # La colonna 'pagata' è la quinta colonna nel nostro foglio
        sheet.update_cell(riga_foglio, 5, True)
        
        return {"status": "successo", "messaggio": "Bolletta segnata come pagata!"}
    except Exception as e:
        return {"status": "errore", "messaggio": str(e)}
