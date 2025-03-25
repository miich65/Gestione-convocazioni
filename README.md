# Arbitro Manager

> 🇮🇹 Web app per arbitri di hockey per gestire le convocazioni, sincronizzare con il calendario Apple e salvare tutto in un database personale.
>
> 🇬🇧 A web app for hockey referees to manage game assignments, sync with Apple Calendar, and store everything in a personal database.

---

## 🇮🇹 Caratteristiche principali
- Inserimento convocazioni tramite form web minimale
- Salvataggio dati in database locale (SQLite)
- Generazione automatica di un file `.ics` per sottoscrizione su Apple Calendar
- Interfaccia leggibile da tutti i dispositivi
- Esecuzione sicura in locale con Docker

## 🇬🇧 Key Features
- Add assignments via minimal web form
- Store data locally in SQLite database
- Automatically generate `.ics` calendar feed for Apple Calendar
- Usable on all devices
- Fully local and secure, Docker-based setup

---

## 🚀 Installazione / Installation

### Requisiti / Requirements
- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

### Avvio rapido / Quick Start
```bash
git clone https://github.com/tuo-utente/arbitro-manager.git
cd arbitro-manager
docker-compose up --build
```

L'app sarà disponibile su `http://localhost:8000`  
The app will be available at `http://localhost:8000`

---

## ✏️ Uso / How to Use

1. Apri `http://localhost:8000`
2. Compila il form con i dati della convocazione
3. Clicca "Salva"
4. Visita `http://localhost:8000/calendario.ics` per ottenere il file del calendario
5. Su Apple Calendar, vai su:
   - `File -> Nuovo calendario in abbonamento -> Incolla URL http://localhost:8000/calendario.ics`

---

## 🗃️ Campi della convocazione / Assignment Fields

| Campo / Field            | Tipo / Type      | Descrizione / Description                  |
|--------------------------|------------------|---------------------------------------------|
| Data e ora inizio        | `datetime`       | Inizio partita                              |
| Orario partenza          | `datetime`       | Quando parti da casa                        |
| Sport                    | `string`         | "inline-hockey" o "ghiaccio"               |
| Squadre (vs)             | `string`         | Es: "Team A vs Team B"                      |
| Luogo                    | `string`         | Indirizzo e città                           |
| Trasferta                | `boolean`        | Trasferta o no                              |
| Indennizzo               | `float`          | Rimborso in euro                            |
| Note                     | `text`           | Es. password per chiudere partita (inline)  |

---

## 📂 Struttura del progetto / Project Structure

```
arbitro-manager/
├── app/
│   ├── main.py              # Backend FastAPI
│   ├── templates/form.html  # Frontend HTML (UI)
│   ├── static/              # (opzionale) CSS/JS
│   └── data/convocazioni.db # Database locale SQLite
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 📈 Futuri sviluppi / Future improvements
- Statistiche e report partite
- Visualizzazione elenco convocazioni
- Modifica/eliminazione convocazioni
- Login utente e backup

---

## 👨‍💻 Autore / Author
**[@miich65](https://github.com/miich65)** – Arbitro & sviluppatore 📊🏒

