FROM python:3.11-slim

WORKDIR /app

# Sin buffer: los print() del bot salen al momento en los logs de Northflank
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "senal_trading_xauusd.py"]