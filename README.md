# 🚛 Feuerwehr Kantinen-Management System

## 🌐 Live-System
- **URL:** https://fw-kantine.de
- **Version:** Production-Ready v2.0
- **Server:** Ubuntu 22.04.5 LTS + Keyhelp

## 🛡️ Sicherheitsfeatures
- MongoDB nur localhost (127.0.0.1)
- Authentifizierung aktiviert
- Production-Mode mit API-Schutz
- Firewall-konfiguriert
- SSL/TLS verschlüsselt

## 🏗️ Architektur
- **Frontend:** React 18 + Tailwind CSS
- **Backend:** FastAPI + Python 3.10
- **Database:** MongoDB 7.0 (nativ)
- **Server:** Nginx Reverse Proxy
- **SSL:** Let's Encrypt

## 📋 Features
- Abteilungsspezifische Menüs
- Frühstücksbestellungen mit Brötchen-Hälften
- Dynamische Mittagspreise
- Mitarbeiter-Verwaltung
- Tägliche Zusammenfassungen
- Drag & Drop Sortierung
- Mobile-optimiert

## 🚀 Deployment
Vollständige Anleitung in `UBUNTU_KEYHELP_DEPLOYMENT.md`

## 🔧 Entwicklung
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn server:app --reload

# Frontend
cd frontend
yarn install
yarn start
```

## 📖 API Dokumentation
- Swagger UI: https://fw-kantine.de/docs
- ReDoc: https://fw-kantine.de/redoc

## 🛡️ Sicherheit
- Alle gefährlichen APIs sind in Production deaktiviert
- MongoDB läuft nur auf localhost
- Sichere Authentifizierung implementiert
- SSL-Verschlüsselung aktiviert

## 📞 Support
Bei Fragen zur Feuerwehr Kantinen-Software wenden Sie sich an das Development-Team.