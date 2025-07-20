# 🔗 OPC UA → MySQL Gateway (Python)

Questo progetto è un gateway Python che consente di acquisire variabili da più PLC tramite protocollo **OPC UA** e salvarle in un database **MySQL**. È pensato per applicazioni industriali di monitoraggio, tracciamento e storicizzazione dati.

IMPORTANTE è un progetto open source e in quanto tale si accettano migliorie e suggerimenti.


## ⚙️ Caratteristiche principali

- ✅ Supporta più PLC OPC UA, ognuno con URL, intervallo di scansione e variabili configurabili.
- 🧠 Lettura di variabili `INT`, `REAL`, `BOOL`, ecc. da nodi OPC UA.
- 🗃️ Salvataggio dei dati in tabelle MySQL, con timestamp e nomi identificativi.
- 📄 Importazione rapida delle variabili da file CSV.
- 🖥️ Interfaccia a menu testuale per configurazione guidata (PLC, DB, variabili, ecc.).
- 🔁 Possibilità di attivare l'avvio automatico dello script all'accensione del PC (Windows).
- 🔒 Configurazione persistente in `config.json`.

## 🛠️ Requisiti

- Python 3.7+
- Librerie:
  - `opcua`
  - `PyMySQL`

Installa le dipendenze con:

```bash
pip install opcua pymysql
