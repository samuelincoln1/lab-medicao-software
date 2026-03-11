# Lab 01 — Análise de Repositórios Populares do GitHub

Este laboratório coleta dados dos repositórios com mais estrelas no GitHub via API GraphQL e realiza uma análise estatística sobre características de qualidade e manutenção desses projetos.

## O que o projeto faz

**Coleta (`collect.py`):** consulta a API GraphQL do GitHub e salva em um arquivo CSV os seguintes atributos de cada repositório:

- Nome, estrelas e linguagem principal
- Idade do repositório e dias desde a última atualização
- Total de Pull Requests aceitas e releases publicadas
- Total de issues abertas e fechadas, além da razão de fechamento

**Análise (`analyze.py`):** lê o CSV gerado e produz gráficos (histogramas e barras) para responder às seguintes questões de pesquisa:

| RQ | Pergunta |
|----|----------|
| RQ01 | Sistemas populares são maduros/antigos? |
| RQ02 | Sistemas populares recebem muita contribuição externa? |
| RQ03 | Sistemas populares lançam releases com frequência? |
| RQ04 | Sistemas populares são atualizados com frequência? |
| RQ05 | Sistemas populares são escritos nas linguagens mais populares? |
| RQ06 | Sistemas populares possuem alto percentual de issues fechadas? |
| RQ07 | Como as métricas variam entre as linguagens mais populares? |

Os gráficos são salvos na pasta `charts/`.

## Pré-requisitos

- Python 3.10+
- Um [Personal Access Token do GitHub](https://github.com/settings/tokens) com escopo `public_repo`

## Instalação

```bash
pip install -r requirements.txt
```

Crie um arquivo `.env` na raiz do projeto com o seu token:

```env
GITHUB_TOKEN=seu_token_aqui
```

## Como rodar

### Coleta padrão (100 repositórios)

```bash
python collect.py
```

Gera o arquivo `results.csv`.

### Análise padrão

```bash
python analyze.py
```

Lê `results.csv` e salva os gráficos em `charts/`.

### Coleta e análise com número customizado de repositórios

Use os argumentos `--target` e `--output` para a coleta e `--input` e `--output-dir` para a análise, sem sobrescrever os dados anteriores:

```bash
# Coleta 1000 repositórios em um arquivo separado
python collect.py --target 1000 --output results_1000.csv

# Analisa o novo arquivo e salva gráficos em pasta separada
python analyze.py --input results_1000.csv --output-dir charts/1000
```

## Estrutura do projeto

```
lab01/
├── collect.py          # Coleta dados da API GraphQL do GitHub
├── analyze.py          # Gera análises e gráficos a partir do CSV
├── requirements.txt    # Dependências Python
├── .env                # Token do GitHub (não versionado)
├── results.csv         # Dados coletados (gerado pelo collect.py)
└── charts/             # Gráficos gerados (gerado pelo analyze.py)
```
