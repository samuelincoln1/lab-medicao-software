# Lab 02 — Qualidade de Repositórios Java Open-Source

Este laboratório coleta os **top-1.000 repositórios Java** do GitHub e analisa sua qualidade interna correlacionando métricas de produto (CBO, DIT, LCOM) calculadas pela ferramenta [CK](https://github.com/mauricioaniche/ck) com características do processo de desenvolvimento.

## Questões de Pesquisa

| RQ | Pergunta |
|----|----------|
| RQ01 | Qual a relação entre a **popularidade** dos repositórios e suas características de qualidade? |
| RQ02 | Qual a relação entre a **maturidade** dos repositórios e suas características de qualidade? |
| RQ03 | Qual a relação entre a **atividade** dos repositórios e suas características de qualidade? |
| RQ04 | Qual a relação entre o **tamanho** dos repositórios e suas características de qualidade? |

## Métricas coletadas

### Processo
| Métrica | Descrição |
|---------|-----------|
| `stars` | Número de estrelas (popularidade) |
| `age_years` | Idade em anos (maturidade) |
| `releases` | Número de releases (atividade) |
| `loc` | Linhas de código Java (tamanho) |
| `comment_lines` | Linhas de comentário (tamanho) |

### Qualidade (via CK)
| Métrica | Descrição |
|---------|-----------|
| `cbo_median` | Mediana de CBO — *Coupling Between Objects* |
| `dit_median` | Mediana de DIT — *Depth of Inheritance Tree* |
| `lcom_median` | Mediana de LCOM — *Lack of Cohesion of Methods* |

## Pré-requisitos

- Python 3.10+
- Java JDK 11+
- Git
- Um [Personal Access Token do GitHub](https://github.com/settings/personal-access-tokens) com escopo `public_repo`

## Instalação

```bash
pip install -r requirements.txt
```

Crie um arquivo `.env` na pasta `lab02/` com o seu token:

```env
GITHUB_TOKEN=seu_token_aqui
```

## Como rodar

### Sprint 1 — Passo 1: Coletar a lista dos 1.000 repositórios

```bash
python collect.py
```

Gera o arquivo `repositories.csv` com: nome, URL, estrelas, data de criação e número de releases.

Parâmetros opcionais:

```bash
python collect.py --target 1000 --output repositories.csv
```

---

### Sprint 1 — Passo 2: CK JAR

O JAR do CK já está disponível no repositório (`ck-0.7.0-jar-with-dependencies.jar`), não sendo necessário nenhum passo adicional.

Caso queira gerar uma versão diferente, compile a partir do código-fonte (requer [Maven](https://maven.apache.org/download.cgi)):

1. Acesse <https://github.com/mauricioaniche/ck/tags> e baixe o código-fonte da tag desejada
2. Extraia o `.zip` e, dentro da pasta extraída, execute:

```bash
mvn package -DskipTests
```

3. O JAR gerado estará em `target/ck-X.X.X-SNAPSHOT-jar-with-dependencies.jar`
4. Copie-o para a pasta `lab02/` e ajuste o argumento `--ck-jar` nos comandos abaixo

---

### Sprint 1 — Passo 3: Coletar métricas de 1 repositório (teste)

```bash
python pipeline.py --ck-jar ck-0.7.0-jar-with-dependencies.jar --limit 1 --output metrics_sample.csv
```

O script irá:
1. Clonar o repositório em um diretório temporário (`--depth 1`)
2. Executar o CK sobre o código Java
3. Contar LOC e linhas de comentário
4. Salvar as métricas em `metrics_sample.csv`

---

### Processamento completo (1.000 repositórios)

```bash
python pipeline.py --ck-jar ck-0.7.0-jar-with-dependencies.jar --output metrics.csv
```

Parâmetros disponíveis:

| Argumento | Descrição |
|-----------|-----------|
| `--ck-jar` | **(Obrigatório)** Caminho para o JAR do CK |
| `--input` | CSV de entrada com a lista de repos (padrão: `repositories.csv`) |
| `--output` | CSV de saída com as métricas (padrão: `metrics.csv`) |
| `--limit N` | Processar apenas os N primeiros repositórios |
| `--keep-clones` | Não apagar os clones após o processamento |

## Estrutura do projeto

```
lab02/
├── collect.py                          # Coleta a lista dos 1.000 repos Java via GitHub GraphQL API
├── pipeline.py                         # Clona repos, executa CK e conta LOC → gera CSV de métricas
├── requirements.txt                    # Dependências Python
├── README.md                           # Este arquivo
├── .env                                # Token do GitHub (não versionado)
├── ck-0.7.0-jar-with-dependencies.jar  # CK JAR (download manual em github.com/mauricioaniche/ck)
├── repositories.csv                    # Lista dos 1.000 repos (gerado pelo collect.py)
├── metrics_sample.csv                  # Métricas de 1 repositório (gerado pelo pipeline.py --limit 1)
└── metrics.csv                         # Métricas de todos os repos (gerado pelo pipeline.py)
```
