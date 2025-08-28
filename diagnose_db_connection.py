#!/usr/bin/env python3
"""
DATENBANK-VERBINDUNGSDIAGNOSE

Prüft welche Datenbank tatsächlich von der App verwendet wird
vs. was in der .env Datei konfiguriert ist.
"""

import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from dotenv import load_dotenv

async def diagnose_db_connection():
    """Diagnose der tatsächlichen DB-Verbindung"""
    
    print("🔍 DATENBANK-VERBINDUNGSDIAGNOSE")
    print("=" * 60)
    
    # 1. Check welche .env Datei gelesen wird
    env_paths = [
        '/app/backend/.env',
        '/app/.env', 
        '.env',
        os.path.expanduser('~/.env')
    ]
    
    print("📄 .ENV DATEIEN SUCHE:")
    for env_path in env_paths:
        if os.path.exists(env_path):
            print(f"   ✅ Gefunden: {env_path}")
            
            # Load this specific .env file
            load_dotenv(env_path)
            
            print(f"      MONGO_URL: {os.environ.get('MONGO_URL', 'NOT SET')}")
            print(f"      DB_NAME: {os.environ.get('DB_NAME', 'NOT SET')}")
        else:
            print(f"   ❌ Nicht gefunden: {env_path}")
    
    # 2. Aktuelle Environment Variables
    print(f"\n🔧 AKTUELLE ENVIRONMENT VARIABLES:")
    mongo_url = os.environ.get('MONGO_URL', 'NOT SET')
    db_name = os.environ.get('DB_NAME', 'NOT SET')
    
    print(f"   MONGO_URL: {mongo_url}")
    print(f"   DB_NAME: {db_name}")
    
    # 3. Extrahiere DB-Namen aus der Connection String
    if mongo_url and mongo_url != 'NOT SET':
        # Parse connection string to extract database name
        if '/' in mongo_url:
            parts = mongo_url.split('/')
            if len(parts) >= 4:  # mongodb://user:pass@host:port/dbname
                connection_db = parts[-1].split('?')[0]  # Remove query params
                print(f"   📊 DB aus Connection String: {connection_db}")
            else:
                print(f"   ⚠️  Keine DB in Connection String erkennbar")
        
        # 4. Teste tatsächliche Verbindung
        print(f"\n🔄 TESTE DATENBANKVERBINDUNG...")
        try:
            client = AsyncIOMotorClient(mongo_url)
            db = client[db_name]
            
            # List all databases to see what's actually available
            admin_db = client.admin
            db_list = await admin_db.list_database_names()
            print(f"   📋 Verfügbare Datenbanken: {db_list}")
            
            # Test connection to configured database
            try:
                collections = await db.list_collection_names()
                print(f"   ✅ Verbindung zu '{db_name}' erfolgreich!")
                print(f"   📁 Collections in '{db_name}': {collections}")
                
                # Count documents in each collection
                if collections:
                    print(f"\n   📊 DOKUMENT-ANZAHL in '{db_name}':")
                    for collection_name in ['departments', 'employees', 'orders']:
                        if collection_name in collections:
                            count = await db[collection_name].count_documents({})
                            print(f"      {collection_name}: {count} Dokumente")
                
            except Exception as e:
                print(f"   ❌ Verbindung zu '{db_name}' fehlgeschlagen: {e}")
            
            # 5. Prüfe ob alte DB noch existiert und verwendet wird
            old_db_names = ['canteen_db', 'fw_kantine_production', 'kantine_production']
            print(f"\n🔍 PRÜFE ALTE DATENBANKEN:")
            
            for old_db_name in old_db_names:
                if old_db_name in db_list:
                    old_db = client[old_db_name]
                    try:
                        old_collections = await old_db.list_collection_names()
                        if old_collections:
                            print(f"   ⚠️  ALTE DB GEFUNDEN: '{old_db_name}'")
                            print(f"      Collections: {old_collections}")
                            
                            # Count documents in old DB
                            for collection_name in ['departments', 'employees', 'orders']:
                                if collection_name in old_collections:
                                    count = await old_db[collection_name].count_documents({})
                                    print(f"      {collection_name}: {count} Dokumente")
                    except Exception as e:
                        print(f"   ❌ Fehler beim Prüfen von '{old_db_name}': {e}")
            
            client.close()
            
        except Exception as e:
            print(f"   ❌ Verbindungsfehler: {e}")
    
    # 6. Check Backend Process Environment
    print(f"\n🖥️  BACKEND PROCESS CHECK:")
    try:
        # Try to find the running backend process
        import subprocess
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        
        backend_processes = []
        for line in result.stdout.split('\n'):
            if 'server.py' in line or 'fastapi' in line or 'uvicorn' in line:
                backend_processes.append(line.strip())
        
        if backend_processes:
            print(f"   ✅ Backend-Prozesse gefunden: {len(backend_processes)}")
            for proc in backend_processes:
                print(f"      {proc}")
        else:
            print(f"   ❌ Keine Backend-Prozesse gefunden")
            
    except Exception as e:
        print(f"   ⚠️  Prozess-Check fehlgeschlagen: {e}")

async def test_specific_database(db_name_to_test):
    """Teste spezifische Datenbank"""
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    
    # Replace database name in connection string
    if '/' in mongo_url and '?' in mongo_url:
        # mongodb://user:pass@host:port/olddb?params -> mongodb://user:pass@host:port/newdb?params
        base_url = '/'.join(mongo_url.split('/')[:-1])  # Remove old DB name
        query_params = '?' + mongo_url.split('?')[1] if '?' in mongo_url else ''
        test_url = f"{base_url}/{db_name_to_test}{query_params}"
    else:
        test_url = mongo_url
    
    print(f"\n🧪 TESTE SPEZIFISCHE DATENBANK: {db_name_to_test}")
    print(f"   Connection: {test_url}")
    
    try:
        client = AsyncIOMotorClient(test_url)
        db = client[db_name_to_test]
        
        collections = await db.list_collection_names()
        print(f"   ✅ Verbindung erfolgreich!")
        print(f"   📁 Collections: {collections}")
        
        # Count documents
        for collection_name in ['departments', 'employees', 'orders']:
            if collection_name in collections:
                count = await db[collection_name].count_documents({})
                print(f"   📊 {collection_name}: {count} Dokumente")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Verbindung fehlgeschlagen: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test specific database
        db_name = sys.argv[1]
        asyncio.run(test_specific_database(db_name))
    else:
        # Full diagnosis
        asyncio.run(diagnose_db_connection())
        
        print(f"\n📝 EMPFOHLENE SCHRITTE:")
        print(f"1. Backend neu starten: sudo supervisorctl restart backend")
        print(f"2. Spezifische DB testen: python3 diagnose_db_connection.py kantine_4600")
        print(f"3. Alte DB testen: python3 diagnose_db_connection.py canteen_db")