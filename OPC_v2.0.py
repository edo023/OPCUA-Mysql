import json
import time
import pymysql
import csv
from opcua import Client

CONFIG_FILE = "config.json"

def carica_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "plc_url": "opc.tcp://192.168.0.10:4840",
            "scan_interval": 1,
            "nodes": [],
            "db": {
                "host": "localhost",
                "user": "root",
                "password": "password",
                "database": "progetto",
                "table": "dati_variabili"
            }
        }

def salva_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def importa_variabili_da_csv(percorso_csv, config):
    try:
        with open(percorso_csv, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            nuove_variabili = []
            esistenti = {v['name'] for v in config['nodes']}
            for row in reader:
                if 'name' in row and 'nodeid' in row and 'type' in row:
                    if row['name'] not in esistenti:
                        nuove_variabili.append({
                            "name": row['name'],
                            "nodeid": row['nodeid'],
                            "type": row['type'].upper()
                        })
            if nuove_variabili:
                config['nodes'].extend(nuove_variabili)
                print(f"✅ {len(nuove_variabili)} variabili importate.")
            else:
                print("⚠️ Nessuna nuova variabile valida trovata.")
    except Exception as e:
        print(f"❌ Errore durante l'importazione del CSV: {e}")

def menu():
    while True:
        print("""
╔════════════════════════════════════╗
║        GATEWAY OPC UA  →  SQL      ║
╚════════════════════════════════════╝
1. Avvia comunicazione
2. Impostazioni
3. Esci
""")
        scelta = input("Scegli un'opzione: ")
        if scelta == "1":
            avvia_gateway()
        elif scelta == "2":
            modifica_config()
        elif scelta == "3":
            print("Uscita.")
            break
        else:
            print("❌ Opzione non valida.")

def modifica_config():
    config = carica_config()
    while True:
        print("""
--- Impostazioni ---
1. PLC - URL e tempo scansione
2. Variabili OPC UA (NodeId)
3. Database
4. Torna al menu principale
""")
        scelta = input("Scegli un'opzione: ")

        if scelta == "1":
            config['plc_url'] = input(f"URL PLC [{config['plc_url']}]: ") or config['plc_url']
            try:
                config['scan_interval'] = float(input(f"Tempo scansione in secondi [{config['scan_interval']}]: ") or config['scan_interval'])
            except:
                print("Valore non valido. Rimane il precedente.")
        elif scelta == "2":
            while True:
                print("""
Variabili attuali:""")
                for i, node in enumerate(config['nodes']):
                    print(f"{i+1}. {node['name']} - {node['nodeid']} ({node['type']})")
                print("""
a. Aggiungi variabile
r. Rimuovi variabile
i. Importa da CSV
t. Torna indietro
""")
                azione = input("Scegli: ").lower()
                if azione == "a":
                    name = input("Nome logico variabile: ")
                    nodeid = input("NodeId completo: ")
                    tipo = input("Tipo (INT, REAL, BOOL): ").upper()
                    config['nodes'].append({"name": name, "nodeid": nodeid, "type": tipo})
                elif azione == "r":
                    try:
                        idx = int(input("Numero da rimuovere: ")) - 1
                        config['nodes'].pop(idx)
                    except:
                        print("Errore nella rimozione.")
                elif azione == "i":
                    percorso = input("Percorso file CSV [variabili.csv]: ") or "variabili.csv"
                    importa_variabili_da_csv(percorso, config)
                elif azione == "t":
                    break
                else:
                    print("Comando non valido.")
        elif scelta == "3":
            db = config['db']
            db['host'] = input(f"Host DB [{db['host']}]: ") or db['host']
            db['user'] = input(f"Utente DB [{db['user']}]: ") or db['user']
            db['password'] = input(f"Password DB [********]: ") or db['password']
            db['database'] = input(f"Nome database [{db['database']}]: ") or db['database']
            db['table'] = input(f"Nome tabella [{db['table']}]: ") or db['table']
        elif scelta == "4":
            break
        else:
            print("Opzione non valida.")

        salva_config(config)
        print("✅ Configurazione salvata.")

def avvia_gateway():
    config = carica_config()
    try:
        client = Client(config['plc_url'])
        client.connect()
        print("✅ Connesso al PLC!")
    except Exception as e:
        print(f"❌ Errore nella connessione al PLC: {e}")
        return

    nodes = []
    for n in config['nodes']:
        try:
            nodes.append({
                "name": n['name'],
                "type": n['type'],
                "node": client.get_node(n['nodeid'])
            })
        except:
            print(f"❌ Errore nel collegare il nodo {n['name']}")

    db_cfg = config['db']

    while True:
        try:
            conn = pymysql.connect(
                host=db_cfg['host'],
                user=db_cfg['user'],
                password=db_cfg['password'],
                database=db_cfg['database']
            )
            with conn.cursor() as cursor:
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS {db_cfg['table']} (
                        nome_variabile VARCHAR(255),
                        valore VARCHAR(255),
                        timestamp DATETIME
                    )
                """)
                conn.commit()
        except Exception as e:
            print(f"❌ Errore connessione DB: {e}")
            time.sleep(3)
            continue

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        for item in nodes:
            try:
                val = item['node'].get_value()
                with conn.cursor() as cursor:
                    cursor.execute(f"""
                        INSERT INTO {db_cfg['table']} (nome_variabile, valore, timestamp)
                        VALUES (%s, %s, %s)
                    """, (item['name'], str(val), timestamp))
                conn.commit()
                print(f"📤 {item['name']}: {val}")
            except Exception as e:
                print(f"⚠️ Errore scrittura DB per {item['name']}: {e}")

        time.sleep(config['scan_interval'])

if __name__ == "__main__":
    menu()
