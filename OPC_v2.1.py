import json
import time
import pymysql
import csv
from opcua import Client

CONFIG_FILE = "config.json"

def carica_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            if 'plcs' not in config:
                config['plcs'] = []
            if 'autostart' not in config:
                config['autostart'] = False
            return config
    except FileNotFoundError:
        return {
            "plcs": [],
            "db": {
                "host": "localhost",
                "user": "root",
                "password": "password",
                "database": "progetto",
                "table": "dati_variabili"
            },
            "autostart": False
        }

def salva_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def importa_variabili_da_csv(percorso_csv, plc):
    try:
        with open(percorso_csv, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            nuove_variabili = []
            esistenti = {v['name'] for v in plc['nodes']}
            for row in reader:
                if 'name' in row and 'nodeid' in row and 'type' in row:
                    if row['name'] not in esistenti:
                        nuove_variabili.append({
                            "name": row['name'],
                            "nodeid": row['nodeid'],
                            "type": row['type'].upper()
                        })
            if nuove_variabili:
                plc['nodes'].extend(nuove_variabili)
                print(f"✅ {len(nuove_variabili)} variabili importate.")
            else:
                print("⚠️ Nessuna nuova variabile valida trovata.")
    except Exception as e:
        print(f"❌ Errore durante l'importazione del CSV: {e}")

def menu():
    while True:
        print("""
╔════════════════════════════════════╗
║     GATEWAY OPC UA  →  SQL (Multi) ║
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
1. Configura PLC
2. Database
3. Avvio automatico
4. Torna al menu principale
""")
        scelta = input("Scegli un'opzione: ")
        if scelta == "1":
            for i, plc in enumerate(config['plcs']):
                print(f"{i+1}. {plc['name']} - {plc['url']}")
            print("a. Aggiungi nuovo PLC")
            print("d. Elimina PLC")
            print("t. Torna indietro")
            scelta_plc = input("Scegli PLC: ")
            if scelta_plc == "a":
                nome = input("Nome PLC: ")
                url = input("URL: ")
                tempo = float(input("Intervallo scansione (s): "))
                config['plcs'].append({"name": nome, "url": url, "scan_interval": tempo, "nodes": []})
            elif scelta_plc == "d":
                try:
                    idx = int(input("Indice del PLC da eliminare: ")) - 1
                    rimosso = config['plcs'].pop(idx)
                    print(f"✅ PLC '{rimosso['name']}' rimosso.")
                except:
                    print("❌ Errore nella rimozione del PLC.")
            elif scelta_plc == "t":
                continue
            else:
                try:
                    idx = int(scelta_plc) - 1
                    plc = config['plcs'][idx]
                    plc['url'] = input(f"URL PLC [{plc['url']}]: ") or plc['url']
                    plc['scan_interval'] = float(input(f"Tempo scansione [{plc['scan_interval']}]: ") or plc['scan_interval'])
                    while True:
                        print("""
Variabili attuali:
""")
                        for i, node in enumerate(plc['nodes']):
                            print(f"{i+1}. {node['name']} - {node['nodeid']} ({node['type']})")
                        print("""
a. Aggiungi variabile
r. Rimuovi variabile
i. Importa da CSV
t. Torna indietro
""")
                        azione = input("Scegli: ").lower()
                        if azione == "a":
                            name = input("Nome: ")
                            nodeid = input("NodeId: ")
                            tipo = input("Tipo (INT, REAL, BOOL): ").upper()
                            plc['nodes'].append({"name": name, "nodeid": nodeid, "type": tipo})
                        elif azione == "r":
                            try:
                                r_idx = int(input("Indice da rimuovere: ")) - 1
                                plc['nodes'].pop(r_idx)
                            except:
                                print("Errore rimozione.")
                        elif azione == "i":
                            percorso = input("Percorso file CSV [variabili.csv]: ") or "variabili.csv"
                            importa_variabili_da_csv(percorso, plc)
                        elif azione == "t":
                            break
                except:
                    print("Indice non valido.")
        elif scelta == "2":
            db = config['db']
            db['host'] = input(f"Host DB [{db['host']}]: ") or db['host']
            db['user'] = input(f"Utente DB [{db['user']}]: ") or db['user']
            db['password'] = input(f"Password DB [********]: ") or db['password']
            db['database'] = input(f"Nome DB [{db['database']}]: ") or db['database']
            db['table'] = input(f"Tabella [{db['table']}]: ") or db['table']

        elif scelta == "3":
            attuale = config.get("autostart", False)
            nuova = input(f"Avvio automatico all'accensione del PC (attuale: {attuale}) [s/n]: ").lower()
            if nuova == "s":
                config["autostart"] = True
                abilita_avvio_automatico()
            elif nuova == "n":
                config["autostart"] = False
                disabilita_avvio_automatico()
            else:
                print("❌ Scelta non valida.")

        elif scelta == "4":
            break
        else:
            print("Opzione non valida.")

        salva_config(config)
        print("✅ Configurazione salvata.")

def avvia_gateway():
    config = carica_config()
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
                        plc_nome VARCHAR(255),
                        nome_variabile VARCHAR(255),
                        valore VARCHAR(255),
                        timestamp DATETIME
                    )
                """)
                conn.commit()
            break
        except Exception as e:
            print(f"❌ Errore connessione DB: {e}")
            time.sleep(3)

    while True:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        for plc in config['plcs']:
            try:
                client = Client(plc['url'])
                client.connect()
                print(f"✅ Connesso a {plc['name']}")

                for node in plc['nodes']:
                    try:
                        nodo = client.get_node(node['nodeid'])
                        valore = nodo.get_value()
                        with conn.cursor() as cursor:
                            cursor.execute(f"""
                                INSERT INTO {db_cfg['table']} (plc_nome, nome_variabile, valore, timestamp)
                                VALUES (%s, %s, %s, %s)
                            """, (plc['name'], node['name'], str(valore), timestamp))
                        conn.commit()
                        print(f"📤 {plc['name']} - {node['name']}: {valore}")
                    except Exception as e:
                        print(f"⚠️ Errore lettura/scrittura {node['name']}: {e}")

                client.disconnect()
            except Exception as e:
                print(f"❌ Connessione fallita per {plc['name']}: {e}")

        time.sleep(min([plc['scan_interval'] for plc in config['plcs']]))


import os
import sys
import shutil

def get_startup_folder():
    return os.path.join(os.getenv('APPDATA'), 'Microsoft\\Windows\\Start Menu\\Programs\\Startup')

def abilita_avvio_automatico():
    nome_script = os.path.basename(sys.argv[0])
    startup_path = os.path.join(get_startup_folder(), "gatewayOPC_autostart.bat")

    with open(startup_path, 'w') as f:
        f.write(f'@echo off\npython "{os.path.abspath(nome_script)}"\n')
    print(f"✅ Avvio automatico abilitato. File creato: {startup_path}")

def disabilita_avvio_automatico():
    startup_path = os.path.join(get_startup_folder(), "gatewayOPC_autostart.bat")
    if os.path.exists(startup_path):
        os.remove(startup_path)
        print("✅ Avvio automatico disabilitato.")
    else:
        print("⚠️ Nessun file di avvio trovato.")


if __name__ == "__main__":
    config = carica_config()
    if config.get("autostart", False):
        avvia_gateway()
    else:
        menu()