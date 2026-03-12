import argparse
import csv
import requests
import json
import os
import time
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

GITHUB_API_URL = "https://api.github.com/graphql"
PAGE_SIZE = 10
DEFAULT_TARGET = 100
DEFAULT_OUTPUT = "results.csv"

QUERY = """
query($cursor: String) {
  search(query: "stars:>1 sort:stars-desc", type: REPOSITORY, first: 10, after: $cursor) {
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ... on Repository {
        nameWithOwner
        createdAt
        pushedAt
        stargazerCount
        primaryLanguage {
          name
        }
        pullRequests(states: MERGED) {
          totalCount
        }
        releases {
          totalCount
        }
        closedIssues: issues(states: CLOSED) {
          totalCount
        }
        openIssues: issues(states: OPEN) {
          totalCount
        }
      }
    }
  }
}
"""


def run_query(variables: dict, retries: int = 3) -> dict:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ValueError(
            "Variável de ambiente GITHUB_TOKEN não definida. "
        )

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    for attempt in range(1, retries + 1):
        response = requests.post(
            GITHUB_API_URL,
            json={"query": QUERY, "variables": variables},
            headers=headers,
            timeout=30,
        )

        if response.status_code in (502, 503, 504):
            wait = attempt * 5
            print(f"  Erro {response.status_code} — aguardando {wait}s antes de tentar novamente ({attempt}/{retries})...")
            time.sleep(wait)
            continue

        response.raise_for_status()

        data = response.json()
        if "errors" in data:
            raise RuntimeError(
                f"Erros retornados pela API GraphQL:\n{json.dumps(data['errors'], indent=2)}"
            )

        return data

    raise RuntimeError(f"Falha após {retries} tentativas.")


def process_repository(node: dict) -> dict:
    now = datetime.now(timezone.utc)

    created_at = datetime.fromisoformat(node["createdAt"].replace("Z", "+00:00"))
    pushed_at = datetime.fromisoformat(node["pushedAt"].replace("Z", "+00:00"))

    age_days = (now - created_at).days
    days_since_push = (now - pushed_at).days

    closed_issues = node["closedIssues"]["totalCount"]
    open_issues = node["openIssues"]["totalCount"]
    total_issues = closed_issues + open_issues
    issue_close_ratio = closed_issues / total_issues if total_issues > 0 else 0.0

    return {
        "name": node["nameWithOwner"],
        "stars": node["stargazerCount"],
        "created_at": node["createdAt"],
        "age_days": age_days,
        "pushed_at": node["pushedAt"],
        "days_since_push": days_since_push,
        "language": node["primaryLanguage"]["name"] if node["primaryLanguage"] else "N/A",
        "merged_prs": node["pullRequests"]["totalCount"],
        "releases": node["releases"]["totalCount"],
        "closed_issues": closed_issues,
        "open_issues": open_issues,
        "total_issues": total_issues,
        "issue_close_ratio": round(issue_close_ratio, 4),
    }


def print_results(repositories: list[dict]) -> None:
    col = {
        "idx":    4,
        "name":   45,
        "stars":  10,
        "age":    13,
        "update": 14,
        "lang":   15,
        "prs":    11,
        "rel":     9,
        "ratio":  18,
    }

    header = (
        f"{'#':<{col['idx']}} "
        f"{'Repositório':<{col['name']}} "
        f"{'Estrelas':>{col['stars']}} "
        f"{'Idade (dias)':>{col['age']}} "
        f"{'Dias s/ update':>{col['update']}} "
        f"{'Linguagem':<{col['lang']}} "
        f"{'PRs aceitas':>{col['prs']}} "
        f"{'Releases':>{col['rel']}} "
        f"{'Issues fechadas':>{col['ratio']}}"
    )
    separator = "-" * len(header)

    print(header)
    print(separator)

    for i, r in enumerate(repositories, 1):
        print(
            f"{i:<{col['idx']}} "
            f"{r['name']:<{col['name']}} "
            f"{r['stars']:>{col['stars']},} "
            f"{r['age_days']:>{col['age']}} "
            f"{r['days_since_push']:>{col['update']}} "
            f"{r['language']:<{col['lang']}} "
            f"{r['merged_prs']:>{col['prs']},} "
            f"{r['releases']:>{col['rel']}} "
            f"{r['issue_close_ratio'] * 100:>{col['ratio'] - 1}.1f}%"
        )


def save_csv(repositories: list[dict], filepath: str) -> None:
    fieldnames = [
        "name", "stars", "created_at", "age_days", "pushed_at",
        "days_since_push", "language", "merged_prs", "releases",
        "closed_issues", "open_issues", "total_issues", "issue_close_ratio",
    ]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(repositories)
    print(f"Dados exportados para: {filepath}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Coleta repositórios populares do GitHub.")
    parser.add_argument("--target", type=int, default=DEFAULT_TARGET, help=f"Número de repositórios a coletar (padrão: {DEFAULT_TARGET})")
    parser.add_argument("--output", type=str, default=DEFAULT_OUTPUT, help=f"Nome do arquivo CSV de saída (padrão: {DEFAULT_OUTPUT})")
    args = parser.parse_args()

    target = args.target
    output_path = os.path.join(os.path.dirname(__file__), args.output)

    print(f"Buscando os {target} repositórios com mais estrelas no GitHub ({PAGE_SIZE} por página)...\n")

    repositories = []
    cursor = None
    page = 1

    while len(repositories) < target:
        print(f"  Página {page} — coletados até agora: {len(repositories)}/{target}")

        data = run_query({"cursor": cursor})
        search = data["data"]["search"]
        nodes = search["nodes"]

        for node in nodes:
            repositories.append(process_repository(node))
            if len(repositories) >= target:
                break

        page_info = search["pageInfo"]
        if not page_info["hasNextPage"]:
            break

        cursor = page_info["endCursor"]
        page += 1
        time.sleep(5)

    print(f"\nTotal de repositórios coletados: {len(repositories)}\n")
    print_results(repositories)
    save_csv(repositories, output_path)
    print("\nConsulta concluída com sucesso!")


if __name__ == "__main__":
    main()
