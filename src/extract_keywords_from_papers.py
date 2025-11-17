import os
import json

from time import sleep
from pathlib import Path
from dotenv import load_dotenv
from color import Colors

# For OpenAI API
from openai import OpenAI

# For converting PDF to text | Json
# from marker.converters.pdf import PdfConverter
# from marker.models import create_model_dict
# from marker.output import text_from_rendered

#  * For RQ 1:
#  * What is the criteria were used for dataset selection:
#  * independently collected or derive an existing dataset?


# ? Preprocess the paper text content
# def preprocess_paper_text(paper_pdf_path: Path) -> str:
#     converter = PdfConverter(
#         artifact_dict=create_model_dict(),
#     )
#     rendered = converter(file_path=paper_pdf_path)
#     text, _, imapges = text_from_rendered(rendered)

#     return text


# ? Prepare for RQ 1 (type of dataset source), RQ 2 (criteria for dataset selection), RQ 3 (goal of research):
def extract_source_of_dataset(paper_pdf: Path, openai_client: OpenAI) -> dict:
    file = openai_client.files.create(
        file=open(paper_pdf, "rb"), 
        purpose="user_data"
    )

    input_text = """
        Please answer 3 questions:
        1. Please extract the source of dataset used in the research paper. Is it collected by the researchers themselves or using existing datasets?

        2. What are the criteria for dataset selection mentioned in the paper if the dataset is collected by the researchers themselves?

        3. What is the goal of the research mentioned in the paper?

        Provide the answer in JSON format with keys.
        The scheme should be like this:
        {
            "dataset_source_type": <collected by researchers or existing dataset or mixed>,
            "existing_source": {
                "name": <name of the existing dataset if the dataset is an existing dataset, else provide null>,
                "description": <description of the existing dataset if the dataset is an existing dataset, else provide null>,
                "url": <url of the existing dataset if the dataset is an existing dataset, else provide null>,
                "selection_criteria": <criteria for dataset selection, provide as a list.>
            },
            "collected_from_github": {
                "url": <the url of the dataset if available else provide null>,
                "selection_criteria": <criteria for selecting repositories from GitHub, provide as a list.>
            },
            "research_goal": <the goal of the research>
        }
    """

    openai_input = [
        {
            'role': 'user',
            'content': [
                {
                    'type': 'input_file',
                    'file_id': file.id
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
        input=openai_input,
    )

    return response.model_dump()


# TODO: For RQ 1 -> Extract the source of dataset used in the paper
# TODO:     between researchers collected by themselves and use existing datasets.
# TODO:     and extract the popular datasets or repositories used in the paper.
# ? For RQ 1:
def statistics_of_dataset_source(paper_text_content: str) -> dict:

    return


# TODO: For RQ 2: -> Extract the criteria for dataset selection:
# TODO:     ex. No. of PRs, Issues, Commits, etc.
# TODO:     Then mapping between the repository selection criteria and the dataset source.
# TODO:     ex. This repository is usually include in a dataset because of criteria A.
# ? For RQ 2:
def extract_criteria_for_dataset_selection(paper_text_content: str) -> dict:
    return


# TODO: For RQ 3: -> Extract the goal of each research work,
# TODO:     Then mapping between the repository selection criteria and the research goal.
# TODO:     ex. If you have this kind of research goal, you can use this criteria for selecting repositories.
# ? For RQ 3:
def extract_goal_of_research(paper_text_content: str) -> dict:
    return


def extract_papers(
    papers_data_path: Path, 
    openai_client: OpenAI,
    save_path: Path
) -> dict:
    if not save_path.exists():
        save_path.mkdir(parents=True, exist_ok=True)

    all_papers_pdf = papers_data_path.glob('*.pdf')
    extracted_paper = save_path.glob('*.json')
    extracted_paper = [p.stem.replace('_extracted', '') for p in extracted_paper]
    # print(json.dumps(extracted_paper, indent=4))

    # all_papers_pdf = list(all_papers_pdf)
    for paper_pdf in all_papers_pdf:
        print(Colors.info("Processing paper:"), paper_pdf)
        paper_name = paper_pdf.stem
        # print("Paper Name:", paper_name)
        if paper_name in extracted_paper:
            print(Colors.warning("Already extracted. Skipping:"), paper_name)
            continue

        sleep(1)  # To avoid rate limiting
        response = extract_source_of_dataset(paper_pdf, openai_client)
        response['output'][-1]['content'][0]['text'] = json.loads(response['output'][-1]['content'][0]['text'])

        # print("Source Type:", json.dumps(json.loads(response['output'][-1]['content'][0]['text']), indent=4, ensure_ascii=False))
        print()
        response_save_path = save_path.joinpath(f'{paper_pdf.stem}_extracted.json')

        with open(response_save_path, 'w', encoding='utf-8') as f:
            json.dump(response, f, ensure_ascii=False, indent=4)

    return


def main():
    load_dotenv()
    current_path = Path.cwd()

    data_path = current_path.joinpath(os.getenv("DATABASE_PATH"))
    openai_api_key = os.getenv("OPENAI_API_KEY")

    openai_client = OpenAI(api_key=openai_api_key)
    print(Colors.info("Data path:"), data_path)

    arxiv_data_path = data_path.joinpath(
        "arxiv", "6_non_slr_survey_papers")
    print(Colors.info("Arxiv data path:"), arxiv_data_path)

    extract_papers_path = data_path.joinpath(
        "arxiv", "extracted_papers"
    )

    extract_papers(
        papers_data_path=arxiv_data_path, 
        openai_client=openai_client,
        save_path=extract_papers_path
    )


if __name__ == "__main__":
    main()
