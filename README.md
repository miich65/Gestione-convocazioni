# RefManager

**RefManager** è un'applicazione web pensata per semplificare la gestione delle convocazioni arbitrali, inizialmente per l'hockey inline e su ghiaccio, ma con la flessibilità necessaria per essere estesa ad altri sport.

Ospitata in: https://ref.mferreira.ch

---

## 🚀 Funzionalità principali

- Inserimento rapido delle convocazioni tramite form moderno
- CRUD completo per convocazioni, sport e categorie
- Calendario esportabile in formato `.ics` compatibile con Apple, Google e Outlook
- Calcolo automatico dell'indennizzo in base a sport e categoria
- Sistema di promemoria (ICS) prima della gara e della partenza
- UI responsive e moderna basata su **Bootstrap 5**
- Modalità di aggiornamento automatizzata con script di deploy

---

## 🛠️ Tecnologie

- **Backend:** Python + FastAPI
- **Frontend:** HTML, Bootstrap, Jinja2
- **Database:** SQLite (persistente in `data/`)
- **Container:** Docker, Docker Compose
- **Calendari:** ICS/WebCal con notifiche automatiche

---

## 🚧 Avvio e Deploy

### 1. Clona il progetto:
```bash
git clone https://github.com/miich65/Gestione-convocazioni.git
cd Gestione-convocazioni
```

### 2. Avvia con Docker:
```bash
docker compose up -d --build
```

L'app sarà accessibile via browser su:
```
http://localhost:8000
```
o su una porta personalizzata (es. 42069).

### 3. Script di Deploy

```bash
cd /var/www/refTI/gestione-convocazioni/Gestione-convocazioni
docker compose down
git pull origin main
docker compose up -d --build
```

---

## 🗓️ Calendario Web

Puoi iscriverti al calendario personale arbitrale tramite:

```
webcal://ref.mferreira.ch/calendario.ics
```

---

## 🌐 Roadmap

- [x] Gestione Sport e Categorie
- [x] Form avanzato convocazioni con auto-calcolo indennizzo
- [ ] Login multi-account con ruoli (admin, arbitro)
- [ ] Parsing automatico da email (Gmail/IMAP)
- [ ] Import/export CSV

---

## 📄 Licenza

Progetto sviluppato da [@miich65](https://github.com/miich65). Uso personale ma pensato per una futura distribuzione nella community arbitrale.

---

**Nome del progetto:** `RefManager`

Semplice. Pulito. Per arbitri.