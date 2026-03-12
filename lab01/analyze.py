import argparse
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

DEFAULT_CSV = "results.csv"
DEFAULT_OUTPUT_DIR = "charts"

TOP_LANGUAGES = ["JavaScript", "Python", "TypeScript", "Java", "C++", "C", "Go", "Rust", "PHP", "Ruby"]

CSV_PATH: str = ""
OUTPUT_DIR: str = ""


def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH)
    df["age_years"] = df["age_days"] / 365.25
    return df


def save_fig(filename: str) -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(path, bbox_inches="tight", dpi=150)
    plt.close()
    print(f"  Gráfico salvo: {path}")


# ──────────────────────────────────────────────
# RQ 01 — Sistemas populares são maduros/antigos?
# ──────────────────────────────────────────────
def rq01(df: pd.DataFrame) -> None:
    print("\n── RQ 01: Idade dos repositórios ──")
    median_years = df["age_years"].median()
    print(f"  Mediana de idade: {median_years:.1f} anos")
    print(f"  Mínimo: {df['age_years'].min():.1f} anos")
    print(f"  Máximo: {df['age_years'].max():.1f} anos")

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(df["age_years"], bins=20, color="#4C72B0", edgecolor="white")
    ax.axvline(median_years, color="red", linestyle="--", label=f"Mediana: {median_years:.1f} anos")
    ax.set_xlabel("Idade (anos)")
    ax.set_ylabel("Quantidade de repositórios")
    ax.set_title("RQ01 — Distribuição de idade dos repositórios")
    ax.legend()
    save_fig("rq01_idade.png")


# ──────────────────────────────────────────────────────────────
# RQ 02 — Sistemas populares recebem muita contribuição externa?
# ──────────────────────────────────────────────────────────────
def rq02(df: pd.DataFrame) -> None:
    print("\n── RQ 02: Pull Requests aceitas ──")
    median_prs = df["merged_prs"].median()
    print(f"  Mediana de PRs aceitas: {median_prs:,.0f}")
    print(f"  Mínimo: {df['merged_prs'].min():,}")
    print(f"  Máximo: {df['merged_prs'].max():,}")

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(df["merged_prs"], bins=30, color="#DD8452", edgecolor="white")
    ax.axvline(median_prs, color="red", linestyle="--", label=f"Mediana: {median_prs:,.0f}")
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.set_xlabel("Total de PRs aceitas")
    ax.set_ylabel("Quantidade de repositórios")
    ax.set_title("RQ02 — Distribuição de Pull Requests aceitas")
    ax.legend()
    save_fig("rq02_pull_requests.png")


# ──────────────────────────────────────────────────────────
# RQ 03 — Sistemas populares lançam releases com frequência?
# ──────────────────────────────────────────────────────────
def rq03(df: pd.DataFrame) -> None:
    print("\n── RQ 03: Total de Releases ──")
    median_rel = df["releases"].median()
    print(f"  Mediana de releases: {median_rel:.0f}")
    print(f"  Mínimo: {df['releases'].min()}")
    print(f"  Máximo: {df['releases'].max()}")

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(df["releases"], bins=30, color="#55A868", edgecolor="white")
    ax.axvline(median_rel, color="red", linestyle="--", label=f"Mediana: {median_rel:.0f}")
    ax.set_xlabel("Total de releases")
    ax.set_ylabel("Quantidade de repositórios")
    ax.set_title("RQ03 — Distribuição de Releases")
    ax.legend()
    save_fig("rq03_releases.png")


# ────────────────────────────────────────────────────────────
# RQ 04 — Sistemas populares são atualizados com frequência?
# ────────────────────────────────────────────────────────────
def rq04(df: pd.DataFrame) -> None:
    print("\n── RQ 04: Tempo desde último push ──")
    median_upd = df["days_since_push"].median()
    print(f"  Mediana: {median_upd:.0f} dias")
    print(f"  Mínimo: {df['days_since_push'].min()} dias")
    print(f"  Máximo: {df['days_since_push'].max()} dias")

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(df["days_since_push"], bins=30, color="#C44E52", edgecolor="white")
    ax.axvline(median_upd, color="blue", linestyle="--", label=f"Mediana: {median_upd:.0f} dias")
    ax.set_xlabel("Dias desde o último push")
    ax.set_ylabel("Quantidade de repositórios")
    ax.set_title("RQ04 — Tempo desde o último push")
    ax.legend()
    save_fig("rq04_atualizacao.png")


# ──────────────────────────────────────────────────────────────────────────
# RQ 05 — Sistemas populares são escritos nas linguagens mais populares?
# ──────────────────────────────────────────────────────────────────────────
def rq05(df: pd.DataFrame) -> None:
    print("\n── RQ 05: Linguagens primárias ──")
    counts = df["language"].value_counts()
    print(counts.to_string())

    top = counts.head(15)
    fig, ax = plt.subplots(figsize=(10, 5))
    top.plot(kind="bar", ax=ax, color="#8172B2", edgecolor="white")
    ax.set_xlabel("Linguagem")
    ax.set_ylabel("Quantidade de repositórios")
    ax.set_title("RQ05 — Linguagens primárias dos repositórios populares")
    ax.tick_params(axis="x", rotation=45)
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    save_fig("rq05_linguagens.png")


# ──────────────────────────────────────────────────────────────────────
# RQ 06 — Sistemas populares possuem alto % de issues fechadas?
# ──────────────────────────────────────────────────────────────────────
def rq06(df: pd.DataFrame) -> None:
    print("\n── RQ 06: Razão de issues fechadas ──")
    median_ratio = df["issue_close_ratio"].median()
    print(f"  Mediana: {median_ratio * 100:.1f}%")
    print(f"  Mínimo: {df['issue_close_ratio'].min() * 100:.1f}%")
    print(f"  Máximo: {df['issue_close_ratio'].max() * 100:.1f}%")

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(df["issue_close_ratio"] * 100, bins=20, color="#64B5CD", edgecolor="white")
    ax.axvline(median_ratio * 100, color="red", linestyle="--", label=f"Mediana: {median_ratio * 100:.1f}%")
    ax.set_xlabel("% de issues fechadas")
    ax.set_ylabel("Quantidade de repositórios")
    ax.set_title("RQ06 — Percentual de issues fechadas")
    ax.legend()
    save_fig("rq06_issues.png")


# ──────────────────────────────────────────────────────────────────────────────────────
# RQ 07 — Linguagens populares vs outras: PRs, releases e frequência de update
# ──────────────────────────────────────────────────────────────────────────────────────
def rq07(df: pd.DataFrame) -> None:
    print("\n── RQ 07 (Bônus): Métricas por linguagem ──")

    df_lang = df[df["language"].isin(TOP_LANGUAGES)].copy()
    df_lang["language"] = pd.Categorical(df_lang["language"], categories=TOP_LANGUAGES, ordered=True)

    metrics = {
        "merged_prs": "PRs aceitas (mediana)",
        "releases": "Releases (mediana)",
    }

    for col, label in metrics.items():
        grouped = df_lang.groupby("language", observed=True)[col].median().dropna()

        fig, ax = plt.subplots(figsize=(10, 5))
        grouped.plot(kind="bar", ax=ax, color="#4C72B0", edgecolor="white")
        ax.set_xlabel("Linguagem")
        ax.set_ylabel(label)
        ax.set_title(f"RQ07 — {label} por linguagem")
        ax.tick_params(axis="x", rotation=45)
        save_fig(f"rq07_{col}_por_linguagem.png")

        print(f"\n  {label}:")
        print(grouped.to_string())


def main() -> None:
    global CSV_PATH, OUTPUT_DIR

    parser = argparse.ArgumentParser(description="Analisa repositórios coletados do GitHub.")
    parser.add_argument("--input", type=str, default=DEFAULT_CSV, help=f"CSV de entrada (padrão: {DEFAULT_CSV})")
    parser.add_argument("--output-dir", type=str, default=DEFAULT_OUTPUT_DIR, help=f"Pasta de saída dos gráficos (padrão: {DEFAULT_OUTPUT_DIR})")
    args = parser.parse_args()

    CSV_PATH = os.path.join(os.path.dirname(__file__), args.input)
    OUTPUT_DIR = os.path.join(os.path.dirname(__file__), args.output_dir)

    print(f"Carregando dados de: {CSV_PATH}")
    df = load_data()
    print(f"Total de repositórios: {len(df)}")

    rq01(df)
    rq02(df)
    rq03(df)
    rq04(df)
    rq05(df)
    rq06(df)
    rq07(df)

    print(f"\nAnálise concluída! Gráficos salvos na pasta '{OUTPUT_DIR}'.")


if __name__ == "__main__":
    main()
