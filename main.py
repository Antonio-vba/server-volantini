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

# Modelli Pydantic
class ScadenzaServer(BaseModel):
    id: int
    nome: str
    importo: float
    dataScadenza: str
    categoria: str
    pagata: bool = False

class NotaServer(BaseModel):
    id: int
    titolo: str
    testo: str

# --- SCADENZE ---
@app.get("/v1/scadenze")
def ottieni_scadenze():
    try:
        client = get_sheets_client()
        if not client: return []
        sheet = client.open("SmartSpesaDB").sheet1
        righe = sheet.get_all_records()
        scadenze = []
        for i, riga in enumerate(righe):
            # Converte correttamente l'importo sostituendo eventuali virgole con punti
            raw_importo = str(riga.get("importo", 0)).replace(",", ".").strip()
            importo_val = float(raw_importo) if raw_importo else 0.0

            scadenze.append({
                "id": i + 1,
                "nome": str(riga.get("nome", "")),
                "importo": importo_val,
                "dataScadenza": str(riga.get("dataScadenza", "")),
                "categoria": str(riga.get("categoria", "Utenze")),
                "pagata": bool(riga.get("pagata", False))
            })
        return scadenze
    except Exception as e:
        print(f"Errore lettura scadenze: {e}")
        return []

@app.post("/v1/scadenze/aggiungi")
def aggiungi_scadenza(scadenza: ScadenzaServer):
    try:
        client = get_sheets_client()
        if not client: return {"status": "errore", "messaggio": "Client non disponibile"}
        sheet = client.open("SmartSpesaDB").sheet1
        
        # Forza esplicitamente pagata a False per le nuove bollette
        sheet.append_row([
            scadenza.nome,
            float(scadenza.importo),
            scadenza.dataScadenza,
            scadenza.categoria,
            False
        ])
        return {"status": "successo"}
    except Exception as e:
        return {"status": "errore", "messaggio": str(e)}

@app.put("/v1/scadenze/{scadenza_id}/paga")
def segna_pagata(scadenza_id: int):
    try:
        client = get_sheets_client()
        if not client: return {"status": "errore", "messaggio": "Client non disponibile"}
        sheet = client.open("SmartSpesaDB").sheet1
        # La riga nel foglio Google è scadenza_id + 1 (tenendo conto dell'intestazione)
        sheet.update_cell(scadenza_id + 1, 5, True)
        return {"status": "successo"}
    except Exception as e:
        return {"status": "errore", "messaggio": str(e)}


# --- NOTE ---
@app.get("/v1/note")
def ottieni_note():
    try:
        client = get_sheets_client()
        if not client: return []
        sheet = client.open("SmartSpesaDB").worksheet("Note")
        righe = sheet.get_all_records()
        note = []
        for i, riga in enumerate(righe):
            note.append({
                "id": i + 1,
                "titolo": str(riga.get("titolo", "")),
                "testo": str(riga.get("testo", ""))
            })
        return note
    except Exception as e:
        print(f"Errore lettura note: {e}")
        return []

@app.post("/v1/note/aggiungi")
def aggiungi_nota(nota: NotaServer):
    try:
        client = get_sheets_client()
        if not client: return {"status": "errore", "messaggio": "Client non disponibile"}
        sheet = client.open("SmartSpesaDB").worksheet("Note")
        sheet.append_row([nota.titolo, nota.testo])
        return {"status": "successo"}
    except Exception as e:
        return {"status": "errore", "messaggio": str(e)}
