import argparse
import csv
import requests
import json
import os
import time
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

GITHUB_API_URL = "https://api.github.com/graphql"
PAGE_SIZE = 10
DEFAULT_TARGET = 1000
DEFAULT_OUTPUT = "repositories.csv"

QUERY = """
query($cursor: String) {
  search(query: "language:Java stars:>100 sort:stars-desc", type: REPOSITORY, first: 10, after: $cursor) {
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ... on Repository {
        nameWithOwner
        url
        createdAt
        stargazerCount
        releases {
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
        raise ValueError("Variável de ambiente GITHUB_TOKEN não definida.")

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
            print(f"  Erro {response.status_code} — aguardando {wait}s ({attempt}/{retries})...")
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
    return {
        "name": node["nameWithOwner"],
        "url": node["url"],
        "stars": node["stargazerCount"],
        "created_at": node["createdAt"],
        "releases": node["releases"]["totalCount"],
    }


def save_csv(repositories: list[dict], filepath: str) -> None:
    fieldnames = ["name", "url", "stars", "created_at", "releases"]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(repositories)
    print(f"Dados exportados para: {filepath}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Coleta top-1000 repositórios Java do GitHub.")
    parser.add_argument("--target", type=int, default=DEFAULT_TARGET,
                        help=f"Número de repositórios a coletar (padrão: {DEFAULT_TARGET})")
    parser.add_argument("--output", type=str, default=DEFAULT_OUTPUT,
                        help=f"Arquivo CSV de saída (padrão: {DEFAULT_OUTPUT})")
    args = parser.parse_args()

    target = args.target
    output_path = os.path.join(os.path.dirname(__file__), args.output)

    print(f"Buscando os {target} repositórios Java com mais estrelas no GitHub...\n")

    repositories = []
    cursor = None
    page = 1

    while len(repositories) < target:
        print(f"  Página {page} — coletados: {len(repositories)}/{target}")

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
        time.sleep(2)

    print(f"\nTotal coletado: {len(repositories)} repositórios\n")
    save_csv(repositories, output_path)
    print("Coleta concluída com sucesso!")


if __name__ == "__main__":
    main()
