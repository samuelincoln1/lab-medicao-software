"""
pipeline.py — Clona repositórios Java, executa a ferramenta CK e coleta métricas
de qualidade (CBO, DIT, LCOM) e de processo (LOC, linhas de comentário).

Uso básico:
    # Processar apenas 1 repositório (para teste):
    python pipeline.py --ck-jar ck-0.7.0-jar-with-dependencies.jar --limit 1 --output metrics_sample.csv

    # Processar todos os 1000 repositórios:
    python pipeline.py --ck-jar ck-0.7.0-jar-with-dependencies.jar --output metrics.csv
"""

import argparse
import csv
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

import pandas as pd

DEFAULT_INPUT = "repositories.csv"
DEFAULT_OUTPUT = "metrics.csv"
DEFAULT_LIMIT = None  # None = processar todos


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

def check_ck_jar(jar_path: str) -> None:
    """Verifica se o CK JAR existe no caminho informado."""
    if not os.path.exists(jar_path):
        print(
            f"CK JAR não encontrado: {jar_path}\n\n"
            "Para gerar o JAR:\n"
            "  1. Baixe o código-fonte em: https://github.com/mauricioaniche/ck/tags\n"
            "  2. Extraia o .zip e, dentro da pasta, execute: mvn package -DskipTests\n"
            "  3. O JAR estará em: target/ck-X.X.X-SNAPSHOT-jar-with-dependencies.jar\n\n"
            "Então informe o caminho com: --ck-jar <caminho/para/ck-jar-with-dependencies.jar>"
        )
        sys.exit(1)


def check_java() -> None:
    """Verifica se o Java está instalado."""
    try:
        subprocess.run(
            ["java", "-version"],
            check=True,
            capture_output=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Java não encontrado. Instale o JDK 11+ e tente novamente.")
        sys.exit(1)


def check_git() -> None:
    """Verifica se o Git está instalado."""
    try:
        subprocess.run(["git", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Git não encontrado. Instale o Git e tente novamente.")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Contagem de LOC
# ---------------------------------------------------------------------------

def count_loc(repo_path: str) -> tuple[int, int]:
    """
    Percorre todos os arquivos .java do repositório e conta:
    - loc: linhas de código (não vazias, não comentários)
    - comment_lines: linhas de comentário (// e /* ... */)

    Retorna (loc, comment_lines).
    """
    loc = 0
    comment_lines = 0

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fname in files:
            if not fname.endswith(".java"):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
                    in_block = False
                    for raw_line in fh:
                        line = raw_line.strip()
                        if not line:
                            continue
                        if in_block:
                            comment_lines += 1
                            if "*/" in line:
                                in_block = False
                        elif line.startswith("//"):
                            comment_lines += 1
                        elif line.startswith("/*") or line.startswith("/**"):
                            comment_lines += 1
                            if "*/" not in line[2:]:
                                in_block = True
                        else:
                            loc += 1
            except OSError:
                pass

    return loc, comment_lines


# ---------------------------------------------------------------------------
# Clone
# ---------------------------------------------------------------------------

def clone_repo(url: str, dest: str, timeout: int = 300) -> bool:
    """Clona o repositório de forma rasa (--depth 1). Retorna True em caso de sucesso."""
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", "--quiet", url, dest],
            check=True,
            capture_output=True,
            timeout=timeout,
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        print(f"    Erro ao clonar {url}: {exc}")
        return False


# ---------------------------------------------------------------------------
# CK
# ---------------------------------------------------------------------------

def run_ck(jar_path: str, repo_path: str, ck_output_dir: str) -> bool:
    """Executa o CK sobre o repositório clonado. Retorna True em caso de sucesso."""
    os.makedirs(ck_output_dir, exist_ok=True)
    try:
        subprocess.run(
            [
                "java", "-jar", jar_path,
                repo_path,       # diretório do repositório
                "false",         # não usar JARs externos
                "0",             # sem limite de arquivos por partição
                ck_output_dir + os.sep,  # diretório de saída (com separador final)
            ],
            check=True,
            capture_output=True,
            timeout=600,
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        print(f"    Erro ao executar CK: {exc}")
        return False


def parse_ck_results(ck_output_dir: str) -> dict:
    """
    Lê o class.csv gerado pelo CK e calcula a mediana de CBO, DIT e LCOM
    sobre todas as classes do projeto.

    Retorna um dict com cbo_median, dit_median, lcom_median (ou None se falhar).
    """
    class_csv = os.path.join(ck_output_dir, "class.csv")
    if not os.path.exists(class_csv):
        return {"cbo_median": None, "dit_median": None, "lcom_median": None}

    try:
        df = pd.read_csv(class_csv)
        df.columns = [c.lower() for c in df.columns]

        cbo_col = next((c for c in df.columns if c.startswith("cbo")), None)
        dit_col = "dit" if "dit" in df.columns else None
        lcom_col = next((c for c in df.columns if c.startswith("lcom")), None)

        return {
            "cbo_median": round(float(df[cbo_col].median()), 4) if cbo_col else None,
            "dit_median": round(float(df[dit_col].median()), 4) if dit_col else None,
            "lcom_median": round(float(df[lcom_col].median()), 4) if lcom_col else None,
        }
    except Exception as exc:
        print(f"    Erro ao parsear CK results: {exc}")
        return {"cbo_median": None, "dit_median": None, "lcom_median": None}


# ---------------------------------------------------------------------------
# Processamento principal
# ---------------------------------------------------------------------------

def process_repo(row: dict, jar_path: str, work_dir: str) -> dict | None:
    """
    Clona o repositório, executa o CK e conta LOC.
    Retorna um dicionário com todas as métricas ou None em caso de falha.
    """
    name = row["name"]
    url = row.get("url") or f"https://github.com/{name}.git"
    repo_slug = name.replace("/", "__")

    clone_dir = os.path.join(work_dir, repo_slug)
    ck_dir = os.path.join(work_dir, f"{repo_slug}__ck")

    print(f"  → Clonando {name} ...")
    if not clone_repo(url, clone_dir):
        return None

    print(f"  → Executando CK em {name} ...")
    if not run_ck(jar_path, clone_dir, ck_dir):
        return None

    print(f"  → Contando LOC em {name} ...")
    loc, comment_lines = count_loc(clone_dir)

    ck_metrics = parse_ck_results(ck_dir)

    created_at_str = row.get("created_at", "")
    try:
        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        age_years = round((datetime.now(timezone.utc) - created_at).days / 365.25, 2)
    except (ValueError, AttributeError):
        age_years = None

    return {
        "name": name,
        "stars": row.get("stars"),
        "age_years": age_years,
        "releases": row.get("releases"),
        "loc": loc,
        "comment_lines": comment_lines,
        "cbo_median": ck_metrics["cbo_median"],
        "dit_median": ck_metrics["dit_median"],
        "lcom_median": ck_metrics["lcom_median"],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Coleta métricas CK + LOC dos repositórios Java listados no CSV de entrada."
    )
    parser.add_argument(
        "--input", type=str, default=DEFAULT_INPUT,
        help=f"CSV com a lista de repositórios (padrão: {DEFAULT_INPUT})"
    )
    parser.add_argument(
        "--output", type=str, default=DEFAULT_OUTPUT,
        help=f"CSV de saída com as métricas (padrão: {DEFAULT_OUTPUT})"
    )
    parser.add_argument(
        "--limit", type=int, default=DEFAULT_LIMIT,
        help="Limitar o número de repositórios processados (útil para testes)"
    )
    parser.add_argument(
        "--ck-jar", type=str, required=True,
        help="Caminho para o CK JAR (ex: --ck-jar ck-0.7.0-jar-with-dependencies.jar)"
    )
    parser.add_argument(
        "--keep-clones", action="store_true",
        help="Não apagar os repositórios clonados após o processamento"
    )
    args = parser.parse_args()

    base_dir = os.path.dirname(__file__)
    input_path = os.path.join(base_dir, args.input)
    output_path = os.path.join(base_dir, args.output)

    check_java()
    check_git()
    check_ck_jar(args.ck_jar)

    if not os.path.exists(input_path):
        print(f"Arquivo de entrada não encontrado: {input_path}")
        print("Execute primeiro: python collect.py")
        sys.exit(1)

    with open(input_path, newline="", encoding="utf-8") as f:
        repos = list(csv.DictReader(f))

    if args.limit:
        repos = repos[: args.limit]

    print(f"\nProcessando {len(repos)} repositório(s)...\n")

    fieldnames = [
        "name", "stars", "age_years", "releases",
        "loc", "comment_lines",
        "cbo_median", "dit_median", "lcom_median",
    ]

    work_dir = tempfile.mkdtemp(prefix="lab02_")
    print(f"Diretório temporário: {work_dir}\n")

    results = []
    try:
        for i, row in enumerate(repos, 1):
            print(f"[{i}/{len(repos)}] {row['name']}")
            metrics = process_repo(row, args.ck_jar, work_dir)
            if metrics:
                results.append(metrics)
                print(
                    f"    OK — LOC={metrics['loc']:,}  "
                    f"CBO={metrics['cbo_median']}  "
                    f"DIT={metrics['dit_median']}  "
                    f"LCOM={metrics['lcom_median']}\n"
                )
            else:
                print(f"    FALHOU — repositório ignorado.\n")

    finally:
        if not args.keep_clones:
            shutil.rmtree(work_dir, ignore_errors=True)
        else:
            print(f"Clones mantidos em: {work_dir}")

    if not results:
        print("Nenhum resultado gerado.")
        sys.exit(1)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n{len(results)} repositório(s) processado(s) com sucesso.")
    print(f"Resultados salvos em: {output_path}")


if __name__ == "__main__":
    main()
