import json
import os
import requests

from bs4 import BeautifulSoup

from pathlib import Path
from dotenv import load_dotenv
from time import sleep
from datetime import datetime

from color import Colors

# ! Limit to 1 request per 3 seconds
def arxiv_query(
    query: str,
    save_path: Path,
    start: int | None = None,
    max_results: int = 200,
) -> None:
    BASE = 'https://export.arxiv.org/api/query'
    start = 0 if start is None else start
    finished: bool = False

    session = requests.Session()

    query = query.replace(' ', '+')

    # api_query = f'(all:"{query}")+AND+cat:{  query}' if query != '' else f'(all:"{query}")'
    if len(query.split()) > 1:
        save_query = '_'.join(query.split())
        # query = '+'.join(query.split())

    with open(save_path.joinpath('progress.txt'), 'r') as file:
        progress = [line.strip() for line in file.readlines()]

    while not finished:
        sleep(3)
        # params = {
        #     'search_query': query,
        #     'start': start,
        #     'max_results': max_results,
        # }
        final_url = f"{BASE}?search_query={query}&start={start}&max_results={max_results}"
        if final_url in progress:
            print(f"{Colors.warning('Skipping already processed query:')} {final_url}")
            continue
        # print(f"ArXiv API URL: {final_url}")

        response = session.get(final_url)
        print(f'Get Response from: {response.url}')
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'lxml')
            entries = soup.find_all('entry')
            if not entries:
                finished = True

            else:
                for entry in entries:
                    title = entry.find('title').text.strip().replace('\n', ' ')
                    authors = [author.find('name').text for author in entry.find_all('author')]
                    summary = entry.find('summary').text.strip().replace('\n', ' ')
                    published = entry.find('published').text
                    link = entry.find('id').text
                    category = [entry.find('arxiv:primary_category')['term']] + [cat['term'] for cat in entry.find_all('category')]
                    page_count = entry.find('arxiv:comment').text if entry.find('arxiv:comment') else None

                    result = {
                        'title': title,
                        'metadata': {
                            'page_count': page_count,
                            'authors': authors,
                            'published': published,
                            'link': link,
                            'category': category,
                        },
                        'data': {
                            'summary': summary,
                        },
                    }

                    save_file_name = '_'.join(title.split())
                    save_file_name = save_file_name[:240] + '.json'
                    if '/' in save_file_name or '\\' in save_file_name:
                        save_file_name = save_file_name.replace('/', '_').replace('\\', '_')
                        
                    if not save_path.exists():
                        save_path.mkdir(parents=True, exist_ok=True)

                    # for index, res in enumerate(results):
                    #     if len(query.split()) > 1:
                    save_index_path = save_path.joinpath(save_file_name)
                    with open(save_index_path.with_suffix('.json'), 'w') as f:
                        json.dump(result, f, indent=4)

                    with open(save_path.joinpath('progress.txt'), 'a') as pf:
                        pf.write(link + '\n')

                    print(f"\t{Colors.success('Saved:')} {title} {Colors.info('at:')} {save_index_path}")
                    # raise Exception('debug')
        else:
            print(f"{Colors.error('error')}: Failed to retrieve data")
            continue
        start += max_results

    print(f"{Colors.success('Completed fetching papers for query:')} {query}")

    return

def paper_selected_files(
    files_path: Path,
    save_path: Path,
) -> None:
    files = files_path.glob('*.json')

    sesession = requests.Session()

    with open(files_path.joinpath('progress.txt'), 'r') as file:
        progress = [line.strip() for line in file.readlines()]

    for file in files:
        sleep(3)
        with open(file, 'r') as f:
            paper = json.load(f)
        
        published = paper.get('metadata', {}).get('published', '')
        published = datetime.strptime(published, '%Y-%m-%dT%H:%M:%SZ').date().isoformat() if published != '' else None

        if not published or published['year'] < 2020:
            continue

        # Only Computer Science papers
        categories = paper.get('metadata', {}).get('category', [])
        if 'cs' not in categories:
            continue

        link = paper.get('metadata', {}).get('link', '')
        title = paper.get('title', 'No Title')

        pdf_link = link.replace('abs', 'pdf') if link != '' else None
        if pdf_link:
            if pdf_link in progress:
                print(f"\t{Colors.warning('Skipping already processed link:')} {pdf_link}")
                continue

            response = sesession.get(pdf_link)
            print(f'Get Response from: {response.url}')

            if response.status_code == 200:
                pdf_path = save_path.joinpath(f"{'_'.join(title.split())[:240]}.pdf")
                with open(pdf_path, 'wb') as pf:
                    pf.write(response.content)
                print(f"\t{Colors.success('Downloaded PDF:')} {title} {Colors.info('at:')} {pdf_path}")
            else:
                print(f"\t{Colors.error('Failed to download PDF for:')} {title} {Colors.info('from:')} {pdf_link}")
                continue

        raise Exception('debug')
    return

def main():
    load_dotenv()
    query: str = 'GitHub Repositories'

    save_path: str = os.getenv('DATABASE_PATH')
    save_path = Path(save_path)

    save_index_path = save_path.joinpath(f'arxiv/references')
    arxiv_query(
        query=query,
        max_results=2800,
        save_path=save_index_path,
    )

    paper_selected_files_path = save_index_path.parent.joinpath('files')
    # paper_selected_files(
    #     files_path=save_index_path,
    #     save_path=paper_selected_files_path
    # )

if __name__ == "__main__":
    main()