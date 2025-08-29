# Canteen Manager - Landing Page

Eine moderne, responsive One-Page Website für das Canteen Management System.

## 🚀 Features

- **Modern & Responsive Design**: Optimiert für alle Geräte
- **Interaktive Animationen**: Smooth Scrolling und Hover-Effekte
- **Kontaktformular**: Direkte Email-Weiterleitung an info@creativey.media
- **App-Preview**: Visuelle Darstellung des Systems
- **SEO-Optimiert**: Meta-Tags und strukturierte Inhalte

## 📁 Dateien

- `index.html` - Haupt-HTML-Datei
- `styles.css` - Alle Styles und Responsive Design
- `script.js` - JavaScript für Interaktionen und Animationen
- `README.md` - Diese Dokumentation

## 🎨 Design

### Farbschema
- **Primär**: #dc2626 (Rot, passend zur Feuerwehr)
- **Sekundär**: #f97316 (Orange)
- **Akzent**: #10b981 (Grün für Erfolg)
- **Text**: #1e293b (Dunkelgrau)
- **Hintergrund**: #f8fafc (Hellgrau)

### Schriftart
- **Haupt**: Inter (Google Fonts)
- **Fallback**: System-Schriften

## 📱 Responsive Breakpoints

- **Desktop**: > 1024px
- **Tablet**: 768px - 1024px
- **Mobile**: < 768px
- **Klein**: < 480px

## 🔧 Setup

### 1. Dateien hochladen
```bash
# Alle Dateien in Webserver-Verzeichnis kopieren
cp -r landing-page/* /var/www/html/
```

### 2. Berechtigungen setzen
```bash
# Leserechte für Webserver
chmod 644 /var/www/html/index.html
chmod 644 /var/www/html/styles.css
chmod 644 /var/www/html/script.js
```

### 3. Screenshots hinzufügen
Die folgenden Screenshot-Dateien müssen noch hinzugefügt werden:
- `screenshot-dashboard.jpg` - Admin Dashboard
- `screenshot-order.jpg` - Bestellmaske
- `screenshot-history.jpg` - Chronologischer Verlauf
- `screenshot-mobile.jpg` - Mobile Ansicht

## 📧 Kontaktformular

Das Kontaktformular verwendet `mailto:`-Links für die Email-Weiterleitung:
- **Empfänger**: info@creativey.media
- **Betreff**: Automatisch generiert
- **Inhalt**: Strukturierte Anfrage-Daten

### Formular-Felder
- Name der Feuerwache (Pflicht)
- Ansprechpartner (Pflicht)
- Email-Adresse (Pflicht)
- Telefonnummer (Optional)
- Anzahl Wachabteilungen (Optional)
- Nachricht (Optional)

## 🌟 Besondere Features

### 1. App-Preview-Animation
- 3D-Effekt mit CSS Transform
- Hover-Interaktionen
- Simulierte App-Oberfläche

### 2. Smooth Scrolling
- Automatisches Scrollen zu Sektionen
- Navbar-Hervorhebung beim Scrollen

### 3. Intersection Observer
- Animationen beim Scrollen
- Performance-optimiert

### 4. Statistik-Counter
- Animierte Zahlen beim Einblenden
- Verschiedene Animationstypen

## 🔄 GitHub Integration

### Repository erstellen
```bash
# Neues Repository für Landing Page
git init
git add .
git commit -m "Initial commit: Canteen Manager Landing Page"
git branch -M main
git remote add origin https://github.com/creativeyMedia/canteen-manager-landing
git push -u origin main
```

### Deployment-Workflow
```bash
# Updates deployen
git add .
git commit -m "Update landing page"
git push origin main

# Auf Server
git pull origin main
```

## 🎯 SEO & Performance

### Meta-Tags
- Title, Description, Keywords
- Open Graph Tags für Social Media
- Viewport für Mobile

### Performance
- Optimierte Bilder (WebP empfohlen)
- Minifizierte CSS/JS für Production
- CDN für Font Awesome und Google Fonts

### Accessibility
- Semantic HTML
- Alt-Tags für Bilder
- Keyboard-Navigation
- Screen Reader kompatibel

## 📊 Analytics (Optional)

Für Tracking können hinzugefügt werden:
- Google Analytics
- Google Tag Manager
- Facebook Pixel

## 🔒 Security

### HTTPS
- SSL-Zertifikat erforderlich
- Secure Headers empfohlen

### Content Security Policy
```html
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; 
               style-src 'self' 'unsafe-inline' fonts.googleapis.com; 
               font-src fonts.gstatic.com;
               script-src 'self' 'unsafe-inline';">
```

## 🐛 Troubleshooting

### Häufige Probleme

1. **Fonts laden nicht**
   - Prüfe Internet-Verbindung
   - Fallback-Fonts werden automatisch verwendet

2. **Formular funktioniert nicht**
   - Email-Client muss installiert sein
   - Browser muss mailto:-Links unterstützen

3. **Animationen ruckeln**
   - CSS-Transform-Optimierung aktivieren
   - `will-change` Property hinzufügen

### Browser-Support
- **Modern Browsers**: Vollständig unterstützt
- **IE 11**: Grundfunktionen ohne Animationen
- **Mobile**: iOS Safari, Android Chrome

## 📝 Anpassungen

### Inhalte ändern
1. Texte in `index.html` bearbeiten
2. Farben in `styles.css` anpassen
3. Animationen in `script.js` modifizieren

### Neue Sektionen hinzufügen
1. HTML-Struktur in `index.html`
2. CSS-Styles in `styles.css`
3. JavaScript-Funktionen in `script.js`
4. Navigation in `nav-links` erweitern

## 📞 Support

Bei Fragen oder Anpassungswünschen:
- **Email**: info@creativey.media
- **Entwicklung**: Vollständige Customization möglich

---

**© 2025 creativey.media - Canteen Manager Landing Page**