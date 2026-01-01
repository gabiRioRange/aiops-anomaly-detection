"""Script para gerar dados sintéticos de métricas com anomalias."""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json


def generate_normal_pattern(size: int, base: float, noise: float) -> np.ndarray:
    """Gera padrão normal com ruído."""
    return base + np.random.normal(0, noise, size)


def inject_spike(data: np.ndarray, position: int, magnitude: float) -> np.ndarray:
    """Injeta um pico (spike) nos dados."""
    data = data.copy()
    data[position] = data[position] * magnitude
    return data


def inject_gradual_increase(data: np.ndarray, start: int, duration: int, factor: float) -> np.ndarray:
    """Injeta aumento gradual (ex: vazamento de memória)."""
    data = data.copy()
    for i in range(duration):
        if start + i < len(data):
            data[start + i] = data[start + i] * (1 + (factor * i / duration))
    return data


def inject_drop(data: np.ndarray, position: int, duration: int) -> np.ndarray:
    """Injeta queda abrupta (ex: crash)."""
    data = data.copy()
    for i in range(duration):
        if position + i < len(data):
            data[position + i] = data[position + i] * 0.1
    return data


def generate_cpu_metrics(hours: int = 24) -> pd.DataFrame:
    """Gera métricas de CPU com padrão diário."""
    points_per_hour = 60  # 1 ponto por minuto
    size = hours * points_per_hour
    
    # Padrão base com sazonalidade diária
    t = np.arange(size)
    base_pattern = 30 + 20 * np.sin(2 * np.pi * t / (24 * points_per_hour))
    noise = np.random.normal(0, 5, size)
    cpu = base_pattern + noise
    
    # Injeta anomalias
    # Spike súbito (ex: job batch)
    cpu = inject_spike(cpu, size // 3, 3.0)
    
    # Picos múltiplos
    for i in range(3):
        pos = size // 2 + i * 100
        if pos < size:
            cpu = inject_spike(cpu, pos, 2.5)
    
    # Limita valores entre 0 e 100
    cpu = np.clip(cpu, 0, 100)
    
    # Cria timestamps
    start_time = datetime.now() - timedelta(hours=hours)
    timestamps = [start_time + timedelta(minutes=i) for i in range(size)]
    
    return pd.DataFrame({
        'timestamp': timestamps,
        'cpu_usage_percent': cpu
    })


def generate_memory_metrics(hours: int = 24) -> pd.DataFrame:
    """Gera métricas de memória com vazamento simulado."""
    points_per_hour = 60
    size = hours * points_per_hour
    
    # Padrão base estável
    memory = generate_normal_pattern(size, 45, 3)
    
    # Injeta vazamento de memória (aumento gradual)
    leak_start = size // 4
    leak_duration = size // 3
    memory = inject_gradual_increase(memory, leak_start, leak_duration, 0.8)
    
    # Alguns picos isolados
    memory = inject_spike(memory, size // 2, 1.8)
    memory = inject_spike(memory, 3 * size // 4, 2.0)
    
    memory = np.clip(memory, 0, 100)
    
    start_time = datetime.now() - timedelta(hours=hours)
    timestamps = [start_time + timedelta(minutes=i) for i in range(size)]
    
    return pd.DataFrame({
        'timestamp': timestamps,
        'memory_usage_percent': memory
    })


def generate_request_metrics(hours: int = 24) -> pd.DataFrame:
    """Gera métricas de requests com picos de tráfego."""
    points_per_hour = 60
    size = hours * points_per_hour
    
    # Padrão base com sazonalidade
    t = np.arange(size)
    base_pattern = 100 + 50 * np.sin(2 * np.pi * t / (24 * points_per_hour))
    noise = np.random.normal(0, 10, size)
    requests = base_pattern + noise
    
    # Pico de tráfego (DDoS simulado ou viral)
    traffic_spike_start = size // 3
    traffic_spike_duration = 120  # 2 horas
    for i in range(traffic_spike_duration):
        if traffic_spike_start + i < size:
            requests[traffic_spike_start + i] *= 5.0
    
    # Queda (downtime)
    downtime_start = 2 * size // 3
    requests = inject_drop(requests, downtime_start, 30)
    
    requests = np.clip(requests, 0, None)
    
    start_time = datetime.now() - timedelta(hours=hours)
    timestamps = [start_time + timedelta(minutes=i) for i in range(size)]
    
    return pd.DataFrame({
        'timestamp': timestamps,
        'requests_per_second': requests
    })


def generate_error_rate_metrics(hours: int = 24) -> pd.DataFrame:
    """Gera métricas de taxa de erro."""
    points_per_hour = 60
    size = hours * points_per_hour
    
    # Taxa de erro normalmente baixa
    error_rate = generate_normal_pattern(size, 0.5, 0.2)
    
    # Evento de erros (bug deploy, database issue)
    error_event_start = size // 2
    error_event_duration = 60
    for i in range(error_event_duration):
        if error_event_start + i < size:
            error_rate[error_event_start + i] = np.random.uniform(15, 25)
    
    # Alguns erros isolados
    error_rate = inject_spike(error_rate, size // 4, 30)
    error_rate = inject_spike(error_rate, 3 * size // 4, 20)
    
    error_rate = np.clip(error_rate, 0, 100)
    
    start_time = datetime.now() - timedelta(hours=hours)
    timestamps = [start_time + timedelta(minutes=i) for i in range(size)]
    
    return pd.DataFrame({
        'timestamp': timestamps,
        'error_rate_percent': error_rate
    })


def save_dataset(output_dir: str = "data/datasets"):
    """Salva datasets sintéticos."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    # Gera datasets
    print("Gerando dados sintéticos...")
    
    cpu_df = generate_cpu_metrics(hours=48)
    memory_df = generate_memory_metrics(hours=48)
    requests_df = generate_request_metrics(hours=48)
    error_df = generate_error_rate_metrics(hours=48)
    
    # Salva CSV
    cpu_df.to_csv(f"{output_dir}/cpu_metrics.csv", index=False)
    memory_df.to_csv(f"{output_dir}/memory_metrics.csv", index=False)
    requests_df.to_csv(f"{output_dir}/request_metrics.csv", index=False)
    error_df.to_csv(f"{output_dir}/error_rate_metrics.csv", index=False)
    
    print(f"✓ CPU metrics: {len(cpu_df)} pontos")
    print(f"✓ Memory metrics: {len(memory_df)} pontos")
    print(f"✓ Request metrics: {len(requests_df)} pontos")
    print(f"✓ Error rate metrics: {len(error_df)} pontos")
    
    # Dataset combinado
    combined = pd.DataFrame({
        'timestamp': cpu_df['timestamp'],
        'cpu_usage_percent': cpu_df['cpu_usage_percent'],
        'memory_usage_percent': memory_df['memory_usage_percent'],
        'requests_per_second': requests_df['requests_per_second'],
        'error_rate_percent': error_df['error_rate_percent']
    })
    
    combined.to_csv(f"{output_dir}/combined_metrics.csv", index=False)
    combined.to_parquet(f"{output_dir}/combined_metrics.parquet", index=False)
    
    print(f"✓ Combined dataset: {len(combined)} pontos")
    print(f"\nArquivos salvos em: {output_dir}/")
    
    # Gera JSON de exemplo para API
    sample_size = 100
    api_example = {
        "series": [
            {
                "resource_id": "pod-web-001",
                "metric_name": "cpu",
                "data": [
                    {
                        "timestamp": str(row['timestamp']),
                        "value": float(row['cpu_usage_percent'])
                    }
                    for _, row in cpu_df.head(sample_size).iterrows()
                ]
            }
        ],
        "method": "isolation-forest",
        "sensitivity": "medium"
    }
    
    with open(f"{output_dir}/api_example_request.json", "w") as f:
        json.dump(api_example, f, indent=2)
    
    print(f"✓ API example request: api_example_request.json")


if __name__ == "__main__":
    save_dataset()
