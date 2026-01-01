#!/usr/bin/env python3
"""
Script de exemplo para usar a API de detecção de anomalias.
"""

import requests
import json
from datetime import datetime, timedelta

def generate_sample_data(points=50, anomaly_at=None):
    """Gera dados de exemplo com possível anomalia."""
    base_value = 10.0
    data = []

    start_time = datetime.now() - timedelta(minutes=points)

    for i in range(points):
        timestamp = start_time + timedelta(minutes=i)

        if anomaly_at and i == anomaly_at:
            value = base_value * 4  # Anomalia
        else:
            # Variação normal
            import random
            value = base_value + random.uniform(-1, 1)

        data.append({
            "timestamp": timestamp.isoformat(),
            "value": round(value, 2)
        })

    return data

def main():
    """Exemplo de uso da API."""

    # Gera dados com anomalia no ponto 30
    sample_data = generate_sample_data(points=50, anomaly_at=30)

    # Payload para a API
    payload = {
        "series": [{
            "resource_id": "example-server",
            "metric_name": "cpu",  # Nome válido da métrica
            "data": sample_data
        }],
        "method": "isolation-forest",
        "sensitivity": "medium"
    }

    try:
        print("🚀 Enviando dados para detecção...")
        print(f"📊 {len(sample_data)} pontos de dados gerados")

        response = requests.post(
            "http://localhost:8000/api/v1/detect",
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            series_result = result["results"][0]

            print("✅ Detecção concluída!")
            print(f"🔍 Método usado: {series_result['method_used']}")
            print(f"📈 Total de pontos: {series_result['total_points']}")
            print(f"🚨 Anomalias detectadas: {series_result['anomaly_count']}")
            print(f"📊 Porcentagem: {series_result['anomaly_percentage']:.2f}%")
            
            # Mostra as anomalias
            anomalies = [a for a in series_result["anomalies"] if a["is_anomaly"]]
            if anomalies:
                print("\n🚨 Anomalias encontradas:")
                for anomaly in anomalies[:5]:  # Mostra primeiras 5
                    print(f"  - Timestamp: {anomaly['timestamp']}, Valor: {anomaly['value']:.2f}, Score: {anomaly['score']:.3f}")
            else:
                print("✅ Nenhuma anomalia detectada nos dados fornecidos.")
        else:
            print(f"❌ Erro na API: {response.status_code}")
            print(response.text)

    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        print("💡 Verifique se a aplicação está rodando em http://localhost:8000")

if __name__ == "__main__":
    main()