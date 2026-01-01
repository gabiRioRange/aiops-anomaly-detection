# Dockerfile para AIOps Anomaly Detection
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar arquivos de configuração
COPY pyproject.toml requirements.txt ./

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY app/ ./app/
COPY templates/ ./templates/
COPY static/ ./static/

# Criar diretório para dados
RUN mkdir -p data logs

# Expor porta
EXPOSE 8000

# Comando para executar
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]