import re
import os
import io
import json
import tarfile
import requests
import traceback

from pypdf import PdfReader
from bs4 import BeautifulSoup
from openai import OpenAI

from pathlib import Path
from dotenv import load_dotenv
from time import sleep
from datetime import datetime

from color import Colors
from doi import doi_query

# ! Limit to 1 request per 3 seconds
# * Paper must be after 2020
# * Paper must have DOI
# * Paper must be in cs.SE category
# This version is the arxiv API query that collects all results without filtering
# Query all papers from software engineering related categories
def arxiv_query_all(
    query: str,
    save_path: Path,
    start: int | None = None,
    max_results: int = 200,
) -> None:
    BASE = 'https://export.arxiv.org/api/query'
    start = 0 if start is None else start
    finished: bool = False

    print(f"{Colors.info('Starting arXiv query for:')} {query} from index {start}")

    if not save_path.exists():
        save_path.mkdir(parents=True, exist_ok=True)

    progress = []
    progress_path = save_path.joinpath('progress.txt')
    if not progress_path.exists():
        with open(progress_path, 'w+') as file:
            file.write('')
    else:
        with open(progress_path, 'r') as file:
            progress = [line.strip() for line in file.readlines()]

    session = requests.Session()
    # based_query = query
    if len(query.split()) > 1:
        # save_query = '_'.join(query.split())
        query = '+'.join(query.split())

    if not save_path.exists():
        save_path.mkdir(parents=True, exist_ok=True)

    while not finished:
        final_url = f"{BASE}?search_query={query}&start={start}&max_results={max_results}"

        sleep(3)
        response = session.get(final_url)
        print(f'Get Response from: {response.url}')

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'lxml')
            entries = soup.find_all('entry')

            if not entries:
                finished = True

            for entry in entries:
                title           = entry.find('title').text.strip().replace('\n', ' ')
                authors         = [author.find('name').text for author in entry.find_all('author')]
                abstract        = (' '.join(entry.find('summary').text.strip().split('\n')).split('. '))
                published_time  = entry.find('published').text
                # published_date  = datetime.strptime(published_time, '%Y-%m-%dT%H:%M:%SZ').date()
                link            = entry.find('link', title='pdf')['href'] if entry.find('link', title='pdf') else None
                source_link     = link.replace('pdf', 'src') if link is not None else None
                categories      = [entry.find('arxiv:primary_category')['term']] + [cat['term'] for cat in entry.find_all('category')]
                # page_count      = entry.find('arxiv:comment').text if entry.find('arxiv:comment') else None
                doi             = entry.find('arxiv:doi').text if entry.find('arxiv:doi') else None
                journal_ref     = entry.find('arxiv:journal_ref').text if entry.find('arxiv:journal_ref') else None

                if title in progress:
                    print(f"{Colors.warning('Skipping already processed paper:')} {title}")
                    continue

                result = {
                    'title': title,
                    'authors': authors,
                    'published_time': published_time,
                    'link': link,
                    'text_source_link': source_link,
                    'categories': categories,
                    'doi': doi,
                    'journal_ref': journal_ref,
                    'abstract': abstract,
                }

                save_file_name = '_'.join(title.split())
                if len(save_file_name) > 240:
                    save_file_name = save_file_name[:240] + '.json'
                else:
                    save_file_name = save_file_name + '.json'

                if '/' in save_file_name or '\\' in save_file_name:
                    save_file_name = save_file_name.replace(
                        '/', '_').replace('\\', '_')
                    
                save_index_path = save_path.joinpath(save_file_name)
                with open(save_index_path.with_suffix('.json'), 'w') as f:
                    json.dump(result, f, indent=4, ensure_ascii=False)

                with open(save_path.joinpath('progress.txt'), 'a') as pf:
                    pf.write(title + '\n')

                print(f"\t{Colors.success('Saved:')} {title} {Colors.info('at:')} {save_index_path}")

            start += max_results

    return

# Since this function are the filtering functions
# Remove old papers (before 2020)
def remove_old_papers(
    papers_path: Path,
    not_old_save_path: Path,
) -> None:
    files = papers_path.glob('*.json')
    if not not_old_save_path.exists():
        not_old_save_path.mkdir(parents=True, exist_ok=True)

    for paper_reference in files:
        with open(paper_reference, 'r') as f:
            paper = json.load(f)

        published_date = datetime.strptime(paper.get('published_time'), '%Y-%m-%dT%H:%M:%SZ').date()

        if published_date.year >= 2020:
            save_path = not_old_save_path.joinpath(paper_reference.name)
            with open(save_path, 'w') as f:
                json.dump(paper, f, indent=4, ensure_ascii=False)

            print(f"\t{Colors.success('Kept recent paper:')} {paper.get('title', 'No Title')} {Colors.info('at:')} {save_path}")
        else:
            print(f"\t{Colors.warning('Removed old paper:')} {paper.get('title', 'No Title')} published on {published_date}")

    return

# Remove papers without DOI
def remove_papers_without_doi(
    papers_path: Path,
    with_doi_save_path: Path,
) -> None:
    files = papers_path.glob('*.json')
    if not with_doi_save_path.exists():
        with_doi_save_path.mkdir(parents=True, exist_ok=True)

    for paper_reference in files:
        with open(paper_reference, 'r') as f:
            paper = json.load(f)

        doi = paper.get('doi', None)

        if doi is not None:
            save_path = with_doi_save_path.joinpath(paper_reference.name)
            with open(save_path, 'w') as f:
                json.dump(paper, f, indent=4, ensure_ascii=False)

            print(f"\t{Colors.success('Kept paper with DOI:')} {paper.get('title', 'No Title')} {Colors.info('at:')} {save_path}")
        else:
            print(f"\t{Colors.warning('Removed paper without DOI:')} {paper.get('title', 'No Title')}")

    return

# Remove papers that were not published in target venues
def remove_papers_not_in_target_venues(
    papers_path: Path,
    in_target_venues_save_path: Path,
) -> None:
    files = papers_path.glob('*.json')
    session = requests.Session()
    TARGET_VENUES = [
        ('ASE', 'Automated Software Engineering'),
        ('FSE', 'Foundations of Software Engineering'),
        ('ICSE', 'International Conference on Software Engineering'),
        ('ISSTA', 'International Symposium on Software Testing and Analysis'),
        ('TOSEM', 'ACM Transactions on Software Engineering and Methodology'),
        ('TSE', 'IEEE Transactions on Software Engineering'),
    ]

    if not in_target_venues_save_path.exists():
        in_target_venues_save_path.mkdir(parents=True, exist_ok=True)

    progress_path = in_target_venues_save_path.joinpath('progress.txt')
    progress = []
    if not progress_path.exists():
        with open(progress_path, 'w+') as f:
            f.write('')
    else:
        with open(progress_path, 'r') as f:
            progress = [line.strip() for line in f.readlines()]

    if not in_target_venues_save_path.exists():
        in_target_venues_save_path.mkdir(parents=True, exist_ok=True)

    for file in files:
        if file.name in progress:
            print(f"{Colors.warning('Skipping already processed paper:')} {file.name}")
            continue
        sleep(3)

        with open(file, 'r') as f:
            paper = json.load(f)

        doi = paper.get('doi', None)
        if doi is None:
            print(f"\t{Colors.warning('Skipping paper without DOI:')} {paper.get('title', 'No Title')}")

            with open(progress_path, 'a') as pf:
                pf.write(file.name + '\n')
            continue

        doi_info = doi_query(doi)
        if doi_info is None:
            print(f"\t{Colors.warning('Removed paper with invalid DOI:')} {paper.get('title', 'No Title')} with DOI: {doi}")

            with open(progress_path, 'a') as pf:
                pf.write(file.name + '\n')
            continue
        doi_full_venue = doi_info.get('container-title', '')

        acronym = None
        if doi_full_venue:
            # Try to find acronyms in parentheses
            acronym_match = re.search(r'\(([A-Z]+)\)', doi_full_venue)
            if acronym_match:
                acronym = acronym_match.group(1)

            doi_full_name = re.sub(r'\s*\(.*?\)\s*', '', doi_full_venue).strip()

        is_target_venue = False
        for venue, full_venue in TARGET_VENUES:
            if (acronym is not None and venue in acronym) or (full_venue in doi_full_name):
                is_target_venue = True
                break

        if not is_target_venue:
            print(f"\t{Colors.warning('Removed paper not in target venues:')} {paper.get('title', 'No Title')} with DOI: {doi}")

            with open(progress_path, 'a') as pf:
                pf.write(file.name + '\n')
            continue

        save_path = in_target_venues_save_path.joinpath(file.name)
        with open(save_path, 'w+') as f:
            json.dump(paper, f, indent=4, ensure_ascii=False)

        with open(progress_path, 'a') as pf:
            pf.write(file.name + '\n')

        print(f"\t{Colors.success('Kept paper in target venues:')} {paper.get('title', 'No Title')} {Colors.info('at:')} {save_path}")


    return

# Remove short papers (less than 8 pages)
def remove_short_papers(
    papers_path: Path,
    long_papers_save_path: Path,
) -> None:
    files = papers_path.glob('*.json')

    if not long_papers_save_path.exists():
        long_papers_save_path.mkdir(parents=True, exist_ok=True)

    progress_path = long_papers_save_path.joinpath('progress.txt')
    progress = []
    if not progress_path.exists():
        with open(progress_path, 'w+') as f:
            f.write('')
    else:
        with open(progress_path, 'r') as f:
            progress = [line.strip() for line in f.readlines()]

    session = requests.Session()
    for file in files:
        file_name = file.name
        if file.name in progress:
            print(f"{Colors.warning('Skipping already processed paper:')} {file.name}")
            continue
        sleep(3)

        with open(file, 'r') as f:
            paper = json.load(f)

        link = paper.get('link', '')
        response = session.get(link)
        print(f'Get Response from: {response.url}')

        if response.status_code == 200:
            if '/' in file_name or '\\' in file_name:
                file_name = file_name.replace('/', '_').replace('\\', '_')

            reader = PdfReader(io.BytesIO(response.content))
            number_of_pages = len(reader.pages)

            if number_of_pages < 8:
                print(f"\t{Colors.warning('Skipping short paper:')} {file.stem} with {number_of_pages} pages")
                print()

                with open(progress_path, 'a') as pf:
                    pf.write(file.name + '\n')
                continue

            save_path = long_papers_save_path.joinpath(f'{file.stem}.pdf')
            with open(save_path, 'wb+') as f:
                f.write(response.content)
            with open(progress_path, 'a') as pf:
                pf.write(file.name + '\n')

            print(f"\t{Colors.success('Kept long paper:')} {paper.get('title', 'No Title')} with {number_of_pages} pages {Colors.info('at:')} {save_path}")

    return

# Remove papers that relevant to systematic literature review (SLR), survey papers, or tool review papers
def remove_slr_and_survey_papers(
    papers_path: Path,
    non_slr_survey_papers_save_path: Path,
    openai_api_key: str,
) -> None:
    files = papers_path.glob('*.pdf')
    openai_client = OpenAI(api_key=openai_api_key)

    if not non_slr_survey_papers_save_path.exists():
        non_slr_survey_papers_save_path.mkdir(parents=True, exist_ok=True)

    for paper_pdf in files:
        print(Colors.info("Processing paper:"), paper_pdf.name)
        paper_name = paper_pdf.stem

        openai_file = openai_client.files.create(
            file=open(paper_pdf, 'rb'),
            purpose='user_data'
        )

        input_text = '''
        If the paper is a systematic literature review (SLR), survey paper, or tool review paper, respond with "YES".
        If the paper is not any of these types, respond with "NO".
        Answer only with "YES" or "NO".
        '''

        openai_input = [
            {
                'role': 'user',
                'content': [
                    {
                        'type': 'input_file',
                        'file_id': openai_file.id
                    },
                    {
                        'type': 'input_text',
                        'text': input_text
                    }
                ]
            }
        ]

        response = openai_client.responses.create(
            model='gpt-5-nano',
            input=openai_input
        )

        # answer = response.choices[0].message['content'].strip().upper()
        answer = response.model_dump()
        # print(Colors.info("Full OpenAI response:"), response.model_dump_json())
        answer = answer['output'][-1]['content'][0]['text'].strip().upper()
        print(Colors.info("OpenAI response:"), answer)

        if answer == 'NO':
            save_path = non_slr_survey_papers_save_path.joinpath(paper_pdf.name)
            with open(paper_pdf, 'rb') as src_file:
                with open(save_path, 'wb') as dest_file:
                    dest_file.write(src_file.read())

            print(f"\t{Colors.success('Kept non-SLR/survey paper:')} {paper_pdf.name} {Colors.info('at:')} {save_path}")
        else:
            print(f"\t{Colors.warning('Removed SLR/survey paper:')} {paper_pdf.name}")
        sleep(1)

    return


def main() -> None:
    load_dotenv()
    current_path = Path().cwd()
    # print(f"Current Path: {current_path}")
    # query: str = 'GitHub Repositories'
    query: list = [
        'GitHub Repositories',
        'GitHub Repository',
        'Software Repositories',
        'Software Repository',
        'Pull Request',
        'Commit',
        'Issue'
    ]

    headers = {
        'User-Agent': os.getenv('USER_AGENT'),
        'Accept': os.getenv('ACCEPT'),
    }

    save_path: str = os.getenv('DATABASE_PATH')
    save_path = current_path.joinpath(save_path)

    for q in query:
        query_path = '_'.join(q.split())
        save_index_path = save_path.joinpath(f'arxiv/1_references/')

    not_old_papers_path = save_path.joinpath('arxiv/2_not_old_papers/')
    # remove_old_papers(
    #     papers_path=save_index_path,
    #     not_old_save_path=not_old_papers_path
    # )

    with_doi_papers_path = save_path.joinpath('arxiv/3_with_doi_papers/')
    # remove_papers_without_doi(
    #     papers_path=not_old_papers_path,
    #     with_doi_save_path=with_doi_papers_path
    # )

    in_target_venues_save_path = save_path.joinpath('arxiv/4_in_target_venues_papers/')
    # remove_papers_not_in_target_venues(
    #     papers_path=with_doi_papers_path,
    #     in_target_venues_save_path=in_target_venues_save_path
    # )

    full_length_papers_path = save_path.joinpath('arxiv/5_full_length_papers/')
    # remove_short_papers(
    #     papers_path=in_target_venues_save_path,
    #     long_papers_save_path=full_length_papers_path
    # )

    non_slr_survey_papers_path = save_path.joinpath('arxiv/6_non_slr_survey_papers/')
    remove_slr_and_survey_papers(
        papers_path=full_length_papers_path,
        non_slr_survey_papers_save_path=non_slr_survey_papers_path,
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )

    return

if __name__ == "__main__":
    main()
