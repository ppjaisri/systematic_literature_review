import os
import json
import requests

from pathlib import Path
from dotenv import load_dotenv

def fetch_papers(
    query: str,
    api_key: str,
    max_results: int = 10,
    sort_by: str = "relevance",
    limit=20,
) -> list:
    all_articles = []
    start = 1

    BASE = "https://ieeexploreapi.ieee.org/api/v1/search/articles"
    while start <= limit:
        params = {
            'apikey': api_key,
            'format': 'json',
            'max_records': max_results,
            'start_record': start,
            'querytext': query,
            'sortfield': sort_by,
        }
        response = requests.get(BASE, params=params)
        data = response.json()
        if response.status_code == 200:
            all_articles.extend(data.get("articles", []))
        else:
            return {"error": "Failed to retrieve data"}
    return all_articles


def main():
    load_dotenv()
    query: str = "machine learning"
    api: str = os.getenv('IEEE_API_KEY')
    save_path: str = os.getenv('DATABASE_PATH')
    save_path = Path(save_path)

    save_index_path = save_path.joinpath(f'ieee/reference/')

    results: list = fetch_papers(query, api, sort_by='oldest')

    if not save_index_path.parent.exists():
        save_index_path.parent.mkdir(parents=True, exist_ok=True)
    with open(save_index_path, 'w') as f:
        json.dump(results, f, indent=4)

if __name__ == "__main__":
    main()
