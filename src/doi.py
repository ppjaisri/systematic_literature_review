import requests
# import json

from time import sleep


def doi_query(
    doi: str, 
    headers: dict | None = None,
    delay: int = 3,
) -> dict | None:
    sleep(delay)
    BASE = 'https://api.crossref.org/works'
    session = requests.Session()
    session.headers.update(headers or {})

    response = session.get(f"{BASE}/{doi}")
    print(response.url)

    if response.status_code == 200:
        response = response.json()

        res = {
            'title': response.get('message').get('title')[0] if response.get('message').get('title') else None,
            'published_date': response.get('message').get('published-print', {}).get('date-parts', [[None]])[0][0],
            'publisher': response.get('message').get('publisher'),
            'container-title': response.get('message').get('container-title')[0] if response.get('message').get('container-title') else None,
            'url': response.get('message').get('URL'),
        }
        # print(json.dumps(res, indent=4))
    
        return res
    else:
        if response.status_code == 404:
            print(f"DOI not found: {doi}")
            return None
        if response.status_code == 429:
            print(f"Rate limit exceeded for DOI {doi}. Waiting for 60 seconds.")
            sleep(delay)
            return doi_query(doi, headers)
        else:
            print(f"Error fetching DOI {doi}: {response.status_code}")
            return None
