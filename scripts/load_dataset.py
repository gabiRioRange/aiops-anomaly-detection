"""Script para carregar datasets externos (ex: Kaggle)."""
import pandas as pd
import requests
import os


def download_kaggle_dataset():
    """
    Instruções para baixar dataset do Kaggle.
    
    Dataset: Cloud Resource Usage Dataset for Anomaly Detection
    URL: https://www.kaggle.com/datasets/programmer3/cloud-resource-usage-dataset-for-anomaly-detection
    """
    print("=" * 70)
    print("DOWNLOAD DATASET KAGGLE")
    print("=" * 70)
    print("\nPara baixar o dataset do Kaggle:")
    print("\n1. Instale o Kaggle CLI:")
    print("   pip install kaggle")
    print("\n2. Configure suas credenciais:")
    print("   - Vá em https://www.kaggle.com/settings/account")
    print("   - Clique em 'Create New API Token'")
    print("   - Salve o kaggle.json em ~/.kaggle/")
    print("\n3. Execute o comando:")
    print("   kaggle datasets download -d programmer3/cloud-resource-usage-dataset-for-anomaly-detection")
    print("\n4. Extraia o arquivo ZIP para data/datasets/")
    print("\nAlternativamente, baixe manualmente de:")
    print("https://www.kaggle.com/datasets/programmer3/cloud-resource-usage-dataset-for-anomaly-detection")
    print("=" * 70)


def load_and_prepare_kaggle_dataset(csv_path: str) -> pd.DataFrame:
    """Carrega e prepara dataset do Kaggle."""
    print(f"\nCarregando dataset: {csv_path}")
    
    df = pd.read_csv(csv_path)
    
    print(f"✓ Dataset carregado: {len(df)} linhas, {len(df.columns)} colunas")
    print(f"\nColunas disponíveis:")
    for col in df.columns:
        print(f"  - {col}")
    
    print(f"\nPrimeiras linhas:")
    print(df.head())
    
    return df


def prepare_for_api(df: pd.DataFrame, resource_id: str = "kaggle-resource-001") -> dict:
    """Prepara dados do Kaggle para formato da API."""
    # Assume colunas: timestamp, cpu, memory, etc.
    
    # Detecta coluna de timestamp
    time_cols = [col for col in df.columns if 'time' in col.lower() or 'date' in col.lower()]
    
    if not time_cols:
        print("⚠️  Coluna de timestamp não encontrada, usando índice")
        df['timestamp'] = pd.date_range(start='2025-01-01', periods=len(df), freq='1min')
        time_col = 'timestamp'
    else:
        time_col = time_cols[0]
        df[time_col] = pd.to_datetime(df[time_col])
    
    # Prepara séries
    series = []
    
    metric_mapping = {
        'cpu': ['cpu', 'CPU'],
        'memory': ['memory', 'mem', 'Memory'],
        'requests': ['request', 'req', 'Request'],
        'error_rate': ['error', 'Error']
    }
    
    for metric_name, keywords in metric_mapping.items():
        # Encontra coluna correspondente
        metric_col = None
        for col in df.columns:
            if any(kw in col for kw in keywords):
                metric_col = col
                break
        
        if metric_col:
            series.append({
                "resource_id": resource_id,
                "metric_name": metric_name,
                "data": [
                    {
                        "timestamp": str(row[time_col]),
                        "value": float(row[metric_col])
                    }
                    for _, row in df.iterrows()
                ]
            })
            print(f"✓ Série preparada: {metric_name} ({len(df)} pontos)")
    
    return {
        "series": series,
        "method": "isolation-forest",
        "sensitivity": "medium"
    }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
        
        if os.path.exists(csv_path):
            df = load_and_prepare_kaggle_dataset(csv_path)
            
            # Prepara para API
            api_data = prepare_for_api(df)
            
            # Salva
            import json
            output_path = "data/datasets/kaggle_api_request.json"
            with open(output_path, "w") as f:
                json.dump(api_data, f, indent=2)
            
            print(f"\n✓ Dados preparados salvos em: {output_path}")
        else:
            print(f"❌ Arquivo não encontrado: {csv_path}")
    else:
        download_kaggle_dataset()
