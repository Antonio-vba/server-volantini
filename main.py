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

class ScadenzaServer(BaseModel):
    id: int
    nome: str
    importo: float
    dataScadenza: str
    categoria: str
    pagata: bool = False
    nota: str = ""

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
            raw_importo = str(riga.get("importo", 0)).strip()
            
            # Pulisce la stringa dell'importo gestendo in modo sicuro sia la virgola che il punto
            if "," in raw_importo and "." in raw_importo:
                if raw_importo.find(",") > raw_importo.find("."):
                    raw_importo = raw_importo.replace(".", "").replace(",", ".")
                else:
                    raw_importo = raw_importo.replace(",", "")
            else:
                raw_importo = raw_importo.replace(",", ".")

            try:
                importo_val = float(raw_importo) if raw_importo else 0.0
            except ValueError:
                importo_val = 0.0

            # Gestione robusta del valore booleano 'pagata'
            val_pagata = riga.get("pagata", False)
            if isinstance(val_pagata, str):
                pagata_bool = val_pagata.strip().lower() in ["true", "1", "yes", "vero"]
            else:
                pagata_bool = bool(val_pagata)

            scadenze.append({
                "id": i + 1,
                "nome": str(riga.get("nome", "")),
                "importo": importo_val,
                "dataScadenza": str(riga.get("dataScadenza", "")),
                "categoria": str(riga.get("categoria", "Generale")),
                "pagata": pagata_bool,
                "nota": str(riga.get("nota", ""))
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
        
        # Converte esplicitamente l'importo in float puro per forzare Google Fogli a memorizzarlo
        # come numero nativo anziché come testo, prevenendo lo spostamento di punti o virgole.
        importo_numerico = float(scadenza.importo)

        sheet.append_row([
            scadenza.nome,
            importo_numerico,
            scadenza.dataScadenza,
            scadenza.categoria,
            False,
            scadenza.nota
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
        # Aggiorna la quinta colonna (corrispondente al campo 'pagata') a True
        sheet.update_cell(scadenza_id + 1, 5, True)
        return {"status": "successo"}
    except Exception as e:
        return {"status": "errore", "messaggio": str(e)}
