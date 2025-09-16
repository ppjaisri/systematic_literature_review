import os
import json
import requests

from bs4 import BeautifulSoup

from time import sleep
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urljoin, urlparse

from color import Colors

def handle_rate_limit(remaining: int, reset: int):
    for _ in range(reset, 0, -1):
        hours, remainder = divmod(reset, 3600)
        minutes, seconds = divmod(remainder, 60)
        print(f"Rate limit exceeded. Remaining: {remaining}. Reset in {hours:02}:{minutes:02}:{seconds:02}", end='\r')
        sleep(1)
    pass

def science_direct_query(
    query: str,
    save_path: Path,
    api_key: str,
    start_year: int = 2000,
    end_year: int = 2024,
    interval: int = 3,
    max_results: int = 100,
) -> list[dict[str, str]]:
    BASE = 'https://api.elsevier.com/content/search/sciencedirect'
    start = 0

    params = {
        'query': query,
        'count': max_results,
        'start': start,
        'date': f'{start_year}-{end_year}'
    }

    headers = {
        'X-ELS-APIKey': api_key,
        'Accept': 'application/json'
    }

    session = requests.Session()
    session.headers.update(headers)

    # initial response
    response = session.get(BASE, params=params)
    print(f"Get Response from: {response.url}")
    if response.status_code == 200:
        remaining = int(response.headers.get('X-RateLimit-Remaining', 1))
        reset = int(response.headers.get('X-RateLimit-Reset', 3600))

        if remaining == 0:
            handle_rate_limit(remaining, reset)
            response = session.get(BASE, params=params)
            print(f"Get Response from: {response.url}")

        data = response.json()
        total_results = int(data.get('search-results', {}).get('opensearch:totalResults', 0))
        # last_page, remainder = divmod(total_results, max_results)
        # if remainder == 0:
        #     last_page += 1

        # all_articles.extend(data.get('search-results', {}).get('entry', []))
        if not save_path.parent.exists():
            save_path.parent.mkdir(parents=True, exist_ok=True)
        save_index_path = save_path.joinpath(f'{query.replace(" ", "_")}_{start}_{start + max_results}.json')
        with open(save_index_path.with_suffix('.json'), 'w') as f:
            json.dump(data, f, indent=4)
        # Retreive all responses
        start += max_results
        while start <= total_results:
            print(f"Progress: Index {start} of {total_results} -> {((start-1)/total_results)*100:.2f}%")
            sleep(interval)
            params['start'] = start
            response = session.get(BASE, params=params)
            print(f"Get Response from: {response.url}")
            remaining = int(response.headers.get('X-RateLimit-Remaining', 1))
            reset = int(response.headers.get('X-RateLimit-Reset', 3600))

            if remaining == 0:
                handle_rate_limit(remaining, reset)
                response = session.get(BASE, params=params)
                print(f"Get Response from: {response.url}")

            if response.status_code == 200:
                data = response.json()
                
                if not save_path.parent.exists():
                    save_path.parent.mkdir(parents=True, exist_ok=True)

                save_index_path = save_path.joinpath(f'{query.replace(" ", "_")}_{start}_{start + max_results}.json')
                with open(save_index_path.with_suffix('.json'), 'w') as f:
                    json.dump(data, f, indent=4)

            start += max_results

        print('Completed fetching all results.')

    else:
        print(f"Error: {response}")
    return

def fetch_papers_file(
    paper_path: Path,
    save_path: Path,
    api_key: str,
) -> None:
    files = list(paper_path.glob('*.json'))

    headers = {
        'X-ELS-APIKey': api_key,
        'Accept': 'text/xml',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0'
    }

    session = requests.Session()
    session.headers.update(headers)

    for file in files:
        with open(file, 'r') as f:
            data = json.load(f)

        progress_file_path = paper_path.parent.joinpath('progress.txt')
        with open(progress_file_path, 'r') as pf:
            progress = pf.read()
        progress = progress.split('\n')

        print(f"Processing file: {file.name}")
        
        list_of_papers = data.get('search-results', {}).get('entry', [])
        for paper in list_of_papers:
            link = paper.get('link', [])[0].get('@href', '')
            if link in progress:
                print(f"\t{Colors.warning('Skipping already processed link:')} {link}")
                continue

            sleep(3)
            if link:
                response = session.get(link)
                print(f"\t{Colors.info('Get Response from:')} {response.url}")

                # print(response)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'lxml')
                    
                    title = soup.find('dc:title').get_text() if soup.find('dc:title') else 'N/A'
                    page_count = soup.find('xocs:web-pdf-page-count').get_text() if soup.find('xocs:web-pdf-page-count') else 'N/A'
                    published = paper.get('prism:coverDate', 'N/A')
                    published_source = paper.get('prism:publicationName', 'N/A')
                    pii = paper.get('pii', 'N/A')
                    abstract = soup.find('dc:description').get_text() if soup.find('dc:description') else 'N/A'
                    sections = soup.find_all('ce:section')
                    
                    # print(f"Title: {title}")
                    # print(f"Page Count: {page_count}")
                    # print(f"Abstract: {abstract}")
                    # Create a safe filename with a max length of 240 chars to stay well under the 255 byte limit
                    file_name = '_'.join(title.split())
                    file_name = file_name[:240] + '.json'
                    if '/' in file_name or '\\' in file_name:
                        file_name = file_name.replace('/', '_').replace('\\', '_')

                    paper_data = {
                        'title': title,
                        'metadata': {
                            'page_count': page_count,
                            'published_date': published,
                            'publisher': published_source,
                            'source_link': link,
                            'pii': pii,
                        },
                        'data': {
                            'abstract': abstract.strip(),
                            'sections': {}
                        },
                    }

                    # Process each section with all its paragraphs
                    for i, section in enumerate(sections):
                        section_title = section.find('ce:section-title')
                        section_title_text = section_title.get_text().strip() if section_title else f"Section {i+1}"

                        # print(f"Section {i + 1}: {section_title_text}")
                        paper_data['data']['sections'][section_title_text] = []

                        # Get all paragraphs in this section
                        paragraphs = section.find_all('ce:para')
                        for _, para in enumerate(paragraphs):
                            for line in para.get_text().strip().split('\n'):
                                if line.strip() != '':
                                    paper_data['data']['sections'][section_title_text].append(line.strip())
                            # print(f"\tParagraph {j + 1}: {para.get_text().strip()}")

                progress.append(link)

            print(f"\t\t{Colors.info('Saving file:')} {file_name} {Colors.info('at:')} {save_path}")
            with open(save_path.joinpath(file_name), 'w+') as f:
                json.dump(paper_data, f, indent=4)

            with open(progress_file_path, 'a') as pf:
                pf.write(f"{link}\n")
            print()

            # raise Exception('debug')

    if not save_path.exists():
        save_path.mkdir(parents=True, exist_ok=True)

    return

def filter_papers(
    files_path: Path,
    save_path: Path,
) -> None:
    files = files_path.glob('*.json')

    for file in files:
        with open(file, 'r') as f:
            data = json.load(f)

        page_count = data.get('metadata', {}).get('page_count', '0')
        if page_count.isdigit() and int(page_count) < 8:
            continue

        

    return

def main():
    load_dotenv()
    API_KEY = os.getenv("ELSEVIER_API_KEY")
    if API_KEY is None:
        raise ValueError("ELSEVIER_API_KEY not found in environment variables.")
    
    query = 'GitHub Repositories'
    paper_ref_path = Path(os.getenv('DATABASE_PATH')).joinpath('science_direct/references')
    # science_direct_query(
    #     query=query,
    #     save_path=paper_ref_path,
    #     api_key=API_KEY,
    #     start_year=2020,
    #     end_year=2025,
    # )

    paper_files_path = paper_ref_path.parent.joinpath('files')
    # fetch_papers_file(
    #     paper_path=paper_ref_path,
    #     save_path=paper_files_path,
    #     api_key=API_KEY
    # )

    filtered_papers_path = paper_ref_path.parent.joinpath('filtered')
    filter_papers(
        files_path=paper_files_path,
        save_path=filtered_papers_path
    )

if __name__ == "__main__":
    main()