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
                
                # Funzione interna per pulire e convertire correttamente il prezzo
                def pulisci_prezzo(valore):
                    if not valore:
                        return 0.0
                    if isinstance(valore, (int, float)):
                        return float(valore)
                    # Se è una stringa, sostituisce l'eventuale virgola con il punto
                    valore_str = str(valore).replace(",", ".").strip()
                    try:
                        return float(valore_str)
                    except ValueError:
                        return 0.0

                # Se il termine cercato corrisponde al nome o al supermercato
                if termine in nome_foglio or termine in supermercato_foglio:
                    risultati.append({
                        "nome": riga.get("nome"),
                        "prezzoPieno": pulisci_prezzo(riga.get("prezzoPieno")),
                        "prezzoOfferta": pulisci_prezzo(riga.get("prezzoOfferta")),
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
