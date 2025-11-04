# Understanding How Software Engineering Research Mine GitHub
## Abstract
GitHub allows other users especially researchers to access to the public repositories.
However, numerous of software projects hosted on the GitHub as GitHub repositories.
Therefore, it presents a challenge for researchers when selecting repositories for empirical studies.
To address this problem, we conducted a systematic literature review (SLR) on how other researchers select repositories for research purpose.
We collected 68,369 software engineering related papers from 6 top-tier venue (ASE, ESEC/FSE, ICSE, ISSTA, TOSEM, TSE
).
After apply quality selection process, we identified 216 unique papers that included explicit selection criteria for GitHub repositories.
Our finding reveal that ... <!-- % Need to fill the result. -->
The results highlight the common characteristic of selected repositories and corresponding research motivation.
It can serve as guidelines for future researchers in construction relevant dataset.
Additionally, this study provide insight for other software developers on how to improve their repositories for the research purpose.
The dataset used in this study is available at [this repository](https://github.com/ppjaisri/systematic_literature_review.git).

## Research Question & Motivation
1. Was the dataset independently collected by the researchers, or was it derived from an existing dataset curated by others?
<br> **Expected answer:** The answer will be a mapping between each type of data collection and paper.
<br> **Motivation:** To inform how popular of each dataset and mapping how coverage of dataset

2. What is the criteria were used for dataset selection?
<br> **Expected answer:** The answer will be a mapping between each terms and the frequently of mention.
<br> **Motivation:** Inform which criteria is the most common and most affect to the repository selection

3. How is the dataset utilized within the scope of the paper?
<br> **Expected answer:** The answer will be a mapping between each term and the purpose or goal of paper.
<br> **Motivation:** Describe which selection criteria is suitable for each type of purpose or goal.

## Quality Assesment Criteria
1. **Match keywords:** Title, abstract, and keywords must relavant to `[GitHub Repository, Software Repository]`
2. **Contains repository selection:** Must explain the criteria of repository selection.
3. **Not a secondary study:** Not a SLR, review, or survey.
4. **Explain in detailed:** Has clear motivations, experimental setups, including experimental environments and dataset information, describe in detail.
5. **Confirm the finding:** Clearly confirm the experimental findings.
6. **Contribute to the community:** Contributions and limitations of the study discussed and contribution to academic or industrial community

## Progress and Plan
### Current Progress
- **Dataset:** Collected 68,369 papers from [ArXiv](https://arxiv.org/)
-  **Selected Paper:** 216 paper from quality assessment criteria

### Next step
---
| Research Question       | Objective |
| ---                     | --- |
| RQ 1: Type of Source    | Extract terms to distinguish between self-collected dataset studies and derived dataset studies. |
|                         | Prepare a statistic result (number of type of source) between self-collected dataset studies and derived dataset studies. |
| RQ 2: Usage Purpose     | Extracted terms from text mining process from the study |
|                         | Mapping the results between mining terms and the frequently of appearance |
| RQ 3: Dataset Selection | Extract the goal of study and grouping into a multiple group |
|                         | Mapping the extracted terms into the group of study's goal and show a statistic result |
---

## Text mining
- Indicate for the self-repository-collection:
  `Pull Requests, Commits, Issues, None-Forking, Stars, Stargazers, Open-Source, Creation Time (Repository), Creation time (GitHub Instances), Stargazers, Repository`

- Indicate for the leverage from others:
  `Previous Dataset, Provided Dataset`

