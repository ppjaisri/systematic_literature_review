import os
import json

from dotenv import load_dotenv
import matplotlib.pyplot as plt

from pathlib import Path
import textwrap


def _format_label(label: str, width: int = 20) -> str:
    lines = textwrap.wrap(label, width=width)
    if len(lines) <= 1:
        return label
    return f"{lines[0]}\n{' '.join(lines[1:])}"


def plot_bar_chart(
    data: dict,
    title: str,
    xlabel: str,
    ylabel: str,
    output_path: Path
) -> None:
    plt.figure(figsize=(10, 7))
    categories = list(data.keys())
    values = [list(counts.values()) for counts in data.values()]

    print("Categories:", categories)
    print("Values:", values)

    categories = sorted(
        categories,
        key=lambda category: sum(data[category].values()),
        reverse=False,
    )
    subcategories = sorted({name for counts in data.values() for name in counts})
    indices = range(len(categories))
    bottoms = [0] * len(categories)

    ax = plt.gca()
    category_labels = categories[:]
    y_positions = list(indices)
    cumulative = [0] * len(category_labels)

    for subcategory in subcategories:
        widths = [data[category].get(subcategory, 0) for category in category_labels]
        ax.barh(y_positions, widths, left=cumulative, label=subcategory)
        cumulative = [left + width for left, width in zip(cumulative, widths)]

    ax.set_yticks(y_positions)
    display_labels = [_format_label(label) for label in category_labels]
    ax.set_yticklabels(display_labels)

    indices = ax.get_xticks().tolist()
    categories = [
        str(int(tick)) if float(tick).is_integer() else f"{tick:.1f}"
        for tick in indices
    ]

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(indices, categories, rotation=45, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()

    return


def prepare_bar_chart_data(
    file_path: Path
) -> tuple[dict, dict]:
    # print(list(file_path.glob("*.json")))
    # print(list(file_path.glob("criteria_grouped_by_goal.json")))
    criteria_per_goal = list(file_path.glob("criteria_grouped_by_goal.json"))[0]
    goal_per_criteria = list(file_path.glob("goal_grouped_by_criteria.json"))[0]

    with open(criteria_per_goal, 'r') as f:
        criteria_per_goal_data = json.load(f)

    criteria_per_goal_stat = {}
    for goal, criteria_dict in criteria_per_goal_data.items():
        if goal not in criteria_per_goal_stat:
            criteria_per_goal_stat[goal] = {}
        for criteria, details in criteria_dict.items():
            criteria_list = criteria.split('_')
            criteria = ''
            for i in criteria_list:
                if i == 'of':
                    criteria += i + ' '
                else:
                    criteria += i.capitalize() + ' '
            criteria = criteria.strip()
            if criteria == 'Queries':
                criteria = 'Specific Queries'
            if criteria not in criteria_per_goal_stat[goal]:
                criteria_per_goal_stat[goal][criteria] = len(details)

    with open(goal_per_criteria, 'r') as f:
        goal_per_criteria_data = json.load(f)

    goal_per_criteria_stat = {}
    for criteria, goals in goal_per_criteria_data.items():
        criteria_list = criteria.split('_')
        criteria = ''
        for i in criteria_list:
            if i == 'of':
                criteria += i + ' '
            else:
                criteria += i.capitalize() + ' '
        criteria = criteria.strip()
        if criteria == 'Queries':
                criteria = 'Specific Queries'
        if criteria not in goal_per_criteria_stat:
            goal_per_criteria_stat[criteria] = {}
        for goal, details in goals.items():
            if goal not in goal_per_criteria_stat[criteria]:
                goal_per_criteria_stat[criteria][goal] = len(details)

    return criteria_per_goal_stat, goal_per_criteria_stat


def main():
    load_dotenv()
    current_path = Path.cwd()
    data_path = current_path.joinpath(os.getenv("DATABASE_PATH"))
    results_path = data_path.joinpath('arxiv')

    criteria_per_goal_stat, goal_per_criteria_stat = prepare_bar_chart_data(results_path)

    print("Criteria per Goal Statistics:", json.dumps(criteria_per_goal_stat, indent=4))
    print("Goal per Criteria Statistics:", json.dumps(goal_per_criteria_stat, indent=4))
    print()
    # return
    plot_bar_chart(
        data=criteria_per_goal_stat,
        title="Number of Selection Criteria per Research Goal",
        xlabel="Number of Selection Criteria",
        ylabel="Research Goals",
        output_path=results_path.joinpath("criteria_per_goal_bar_chart.png")
    )

    plot_bar_chart(
        data=goal_per_criteria_stat,
        title="Number of Research Goals per Selection Criteria",
        xlabel="Number of Research Goals",
        ylabel="Selection Criteria",
        output_path=results_path.joinpath("goal_per_criteria_bar_chart.png")
    )
    return

if __name__ == "__main__":
    main()