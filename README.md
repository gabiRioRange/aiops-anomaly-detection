# AIOps Anomaly Detection Service

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg)](https://docker.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Mini serviço AIOps para detecção de anomalias em métricas de infraestrutura (CPU, memória, requests) usando Python, FastAPI e múltiplos métodos de detecção.

## 🚀 Features

- **Múltiplos Métodos de Detecção**:
  - **Estatísticos**: Z-score, Moving Average
  - **Machine Learning**: Isolation Forest, Local Outlier Factor (LOF), Prophet
  - **Avançados**: dtaianomaly (Matrix Profile)

- **Conceito AIOps/Grok**:
  - Agrupamento inteligente de anomalias em eventos
  - Redução de ruído de alertas
  - Priorização automática baseada em score, duração e impacto

- **API REST com FastAPI**:
  - Endpoints assíncronos de alta performance
  - Documentação automática (Swagger/OpenAPI)
  - Validação com Pydantic

- **Dashboard Web Interativo**:
  - Interface gráfica para detecção em tempo real
  - Gráficos visuais com Chart.js
  - Formulário intuitivo para testes
  - Resultados instantâneos

- **Persistência**:
  - SQLite/PostgreSQL com SQLAlchemy async
  - Histórico de detecções
  - Eventos agrupados

- **Ferramentas de Desenvolvimento**:
  - Linting com Ruff
  - Formatação com Black
  - Testes com pytest e cobertura
  - Docker support

### Configuração

Copie o arquivo de exemplo e ajuste as configurações:

```bash
cp .env.example .env
```

Variáveis importantes:
- `DATABASE_URL`: URL do banco de dados (SQLite por padrão)
- `DEBUG`: Ativar modo debug
- `SENSITIVITY_*`: Ajustar sensibilidade dos detectores

## 🔧 Instalação

### Opção 1: Docker (Recomendado)

```bash
# Clone o repositório
git clone https://github.com/gabiRioRange/aiops-anomaly-detection
cd aiops-anomaly-detection

# Build e execute com Docker
docker-compose up --build

# A aplicação estará disponível em http://localhost:8000
```

### Opção 2: Instalação Local

```bash
# Clone o repositório
git clone https://github.com/gabiRioRange/aiops-anomaly-detection
cd aiops-anomaly-detection

# Instale com pip
pip install -e .

# Ou com poetry
poetry install

# Para desenvolvimento
pip install -e ".[dev]"
# ou
poetry install --with dev
```

## 🚀 Uso

### Dashboard Web (Interface Gráfica)

A maneira mais fácil de usar o sistema é através do **dashboard web**:

1. **Execute a aplicação**:
   ```bash
   # Com Docker
   docker-compose up --build

   # Ou localmente
   uvicorn app.main:app --reload
   ```

2. **Acesse o dashboard**: Abra `http://localhost:8000/dashboard` no navegador

3. **Use a interface**:
   - Insira dados de métricas (CPU, memória, etc.)
   - Selecione o método de detecção
   - Ajuste a sensibilidade
   - Visualize anomalias em tempo real no gráfico

### API REST

Para integração programática:

```bash
# Execute a aplicação
uvicorn app.main:app --reload

# Ou use o script
aiops

# Acesse a documentação interativa
open http://localhost:8000/docs
```

#### Exemplo de Request

```python
import requests

# Dados de exemplo com anomalia
data = {
    "series": [{
        "resource_id": "web-server-01",
        "metric_name": "cpu_usage",
        "data": [
            {"timestamp": "2024-01-01T00:00:00", "value": 10.1},
            {"timestamp": "2024-01-01T00:01:00", "value": 10.5},
            {"timestamp": "2024-01-01T00:02:00", "value": 11.2},
            {"timestamp": "2024-01-01T00:03:00", "value": 10.8},
            {"timestamp": "2024-01-01T00:04:00", "value": 10.3},
            {"timestamp": "2024-01-01T00:05:00", "value": 10.7},
            {"timestamp": "2024-01-01T00:06:00", "value": 45.2},  # Anomalia!
            {"timestamp": "2024-01-01T00:07:00", "value": 10.4},
            {"timestamp": "2024-01-01T00:08:00", "value": 10.6},
            {"timestamp": "2024-01-01T00:09:00", "value": 10.9}
        ]
    }],
    "method": "isolation-forest",
    "sensitivity": "medium"
}

response = requests.post("http://localhost:8000/api/v1/detect", json=data)
result = response.json()

#### Exemplo Completo

Execute o script de exemplo que gera dados sintéticos e demonstra a detecção:

```bash
python scripts/example_usage.py
```

Este script:
- Gera 50 pontos de dados com uma anomalia artificial
- Envia para a API de detecção
- Mostra os resultados detalhados

### Monitoramento em Tempo Real

### Monitoramento em Tempo Real

Para monitorar métricas em tempo real:

```python
import time
from datetime import datetime

def monitor_metric():
    data_points = []
    
    while True:
        # Coleta nova métrica
        current_value = get_current_cpu_usage()  # Sua função
        data_points.append({
            "timestamp": datetime.now().isoformat(),
            "value": current_value
        })
        
        # Mantém apenas últimas 100 medições
        if len(data_points) > 100:
            data_points = data_points[-100:]
        
        # Detecta anomalias quando tiver dados suficientes
        if len(data_points) >= 10:
            payload = {
                "series": [{
                    "resource_id": "my-server",
                    "metric_name": "cpu_usage",
                    "data": data_points
                }],
                "method": "isolation-forest",
                "sensitivity": "medium"
            }
            
            response = requests.post("http://localhost:8000/api/v1/detect", json=payload)
            result = response.json()
            
            anomaly_count = result["results"][0]["anomaly_count"]
            if anomaly_count > 0:
                print(f"🚨 ALERTA: {anomaly_count} anomalias detectadas!")
        
        time.sleep(60)  # Verifica a cada minuto
```

## 🔍 Métodos de Detecção

O sistema suporta múltiplos algoritmos para detecção de anomalias:

| Método | Tipo | Descrição | Quando Usar |
|--------|------|-----------|-------------|
| **isolation-forest** | ML | Isolation Forest - eficiente para high-dimensional data | Dados complexos, boa performance geral |
| **z-score** | Estatístico | Desvio padrão da média | Séries simples, baseline rápida |
| **lof** | ML | Local Outlier Factor | Agrupamentos locais de anomalias |
| **prophet** | ML | Facebook Prophet para séries temporais | Dados sazonais, tendências |
| **moving-average** | Estatístico | Média móvel | Detecção de mudanças graduais |
| **dtai-auto** | Avançado | Matrix Profile (se disponível) | Padrões complexos em séries longas |

### Sensibilidade

- **low**: Menos falsos positivos, pode perder anomalias sutis
- **medium**: Equilíbrio recomendado
- **high**: Mais sensível, mais falsos positivos

## 🧪 Testes

```bash
# Execute todos os testes
pytest

# Com cobertura
pytest --cov=app --cov-report=html

# Testes específicos
pytest tests/test_api.py -v
```

## �️ Desenvolvimento

### Comandos Úteis

```bash
# Instalar dependências de dev
make install-dev

# Formatar código
make format

# Executar linting
make lint

# Executar testes
make test

# Executar aplicação
make run

# Docker
make docker-build
make docker-run
```

### Estrutura do Projeto

```
projeto-aiops/
├── app/                    # Código da aplicação
│   ├── api/               # Endpoints REST
│   ├── core/              # Configurações e utilitários
│   ├── db/                # Modelos e sessão do banco
│   ├── detection/         # Algoritmos de detecção
│   └── main.py            # Ponto de entrada
├── templates/             # Templates HTML
├── static/                # Arquivos estáticos
├── tests/                 # Testes
├── data/                  # Dados de exemplo
├── logs/                  # Logs da aplicação
├── docker-compose.yml     # Configuração Docker
├── Dockerfile            # Imagem Docker
├── pyproject.toml        # Configuração do projeto
└── requirements.txt      # Dependências
```


### Adicionando Novos Detectores

1. Implemente a classe em `app/detection/ml_detectors.py`
2. Adicione ao dicionário `methods` em `app/detection/engine.py`
3. Atualize os testes em `tests/test_detection.py`
4. Documente no README

## 📄 Licença

Este projeto está sob a licença MIT.
