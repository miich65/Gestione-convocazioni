# Dockerfile
FROM python:3.11-slim

# Crea cartella app e copia contenuto
WORKDIR /app
COPY ./app /app

# Installa dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Espone la porta
EXPOSE 8000

# Comando di avvio
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
