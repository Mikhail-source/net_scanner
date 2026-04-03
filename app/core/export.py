import csv
from pathlib import Path
from typing import List, Dict

def export_data(data: List[Dict], filename: str = "scan_results.csv"):
    """Экспортирует результаты сканирования в CSV"""
    if not data:
        return False
    
    filepath = Path.cwd() / filename
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        return True
    except Exception as e:
        print(f"Export error: {e}")
        return False