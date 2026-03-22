# LH Nautical — Desafio Lighthouse

Solução completa do Desafio Técnico de Dados & IA da Indicium Academy.  
**Autor:** Patrick Wöhrle Guimarães | **Data:** Março de 2026  
**Ferramentas:** Python 3 · DuckDB · Pandas · Scikit-learn · Streamlit
---

## Entregáveis

| Descrição | Link |
|---|---|
| Notebook Principal | [`2026_Desafio_Lighthouse_Dados.ipynb`](2026_Desafio_Lighthouse_Dados.ipynb) |
| Dashboard Interativo (Streamlit) | [`streamlit_app.py`](streamlit_app.py) |
| Sumário Executivo (PDF) | [`sumario_executivo.pdf`](sumario_executivo.pdf) |
---

---

## Estrutura do Projeto no Github
````
desafiolighthouse_2026/ 
├── 2026_Desafio_Lighthouse_Dados_&_AI.ipynb # Notebook principal 
├── streamlit_app.py # Dashboard interativo 
├── requirements.txt # Dependências 
├── vendas_2023_2024.csv # Dataset de vendas 
├── produtos_raw.csv # Catálogo de produtos 
├── custos_importacao.json # Custos de importação 
├── clientes_crm.json # Dados de CRM 
├── prejuizo_agregado.csv # Resultado Q04 
├── clientes_elite.csv # Resultado Q05 
├── categorias_elite.csv # Resultado Q05 
├── media_vendas_dia_semana.csv # Resultado Q06 
├── previsao_demanda.csv # Resultado Q07 
└── produtos_similares.csv # Resultado Q08
````

---

## Como Executar

1.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Execute o dashboard:**
    ```bash
    streamlit run streamlit_app.py
    ```

---

## Questões Respondidas

### Q1 — EDA (Análise Exploratória de Dados)
*   **Resultados:** 9.895 registros · 6 colunas · Período: 2023-2024 · Mínimo: R$ 294,50 · Máximo: R$ 2.222.973,00 · Média: R$ 263.797,83 · Zero nulos
*   **Conclusão:** Dataset com boa integridade, mas requer tratamento de outliers e padronização de datas.

### Q2 — Normalização de Produtos
*   **Resultado:** 7 duplicatas removidas (157 → 150 produtos). Categorias padronizadas em eletrônicos, propulsão e ancoragem.
*   **Metodologia:** Normalização por substrings (eletron, propul, ancor) captura variações como Eletronicoz e E L E T R Ô N I C O S.

### Q3 — Normalização de Custos de Importação
*   **Resultado:** 1.260 registros tabulares a partir do JSON aninhado, com datas normalizadas (format=mixed, dayfirst=True) e ordenadas por produto e data.

### Q4 — Análise de Margem com Câmbio BCB/PTAX
*   **Resultados:**
    *   62,8% das transações abaixo do custo
    *   Produto 72 concentra R$ 39,8 milhões em prejuízo (63,15% de perda)
    *   Prejuízo total: R$ 182,2 milhões
*   **Metodologia:**
    *   API BCB/PTAX com fallback de 7 dias úteis
    *   Custo vigente: último preço com start_date <= data_venda
    *   Validação cruzada Python vs SQL

### Q5 — Análise de Clientes Elite
*   **Resultados:**
    *   Top 10 clientes com ticket médio entre R$ 290.063 e R$ 336.859
    *   Categoria mais vendida: propulsão (6.030 itens)
    *   Todos os top 10 clientes compram nas 3 categorias core
*   **Critério:** Diversidade >= 3 categorias, ordenado por ticket médio decrescente

### Q6 — Dimensão de Calendário
*   **Resultados:**
    *   Pior dia de vendas: Domingo (R$ 3.229.614,16)
    *   Melhor dia de vendas: Sexta-feira (R$ 3.776.151,25)
*   **Metodologia:** `generate_series` + `LEFT JOIN` + `COALESCE` para incluir dias sem venda

### Q7 — Previsão de Demanda
*   **Resultados:**
    *   MAE = 0,9958 unidades
    *   Previsão para primeira semana de janeiro: 0 unidades (real = 0)
    *   Total de vendas em janeiro: 17 unidades
*   **Modelo:** Média Móvel Simples com janela de 7 dias. Demanda intermitente do produto (apenas 2 dias com venda) justifica a previsão zero.

### Q8 — Sistema de Recomendação
*   **Resultados:**
    *   Produto mais similar ao GPS Garmin Vortex Maré Drift: Motor de Popa Volvo Magnum 276HP (ID 94, similaridade 0,8696)
    *   **Top 5 produtos similares:**
        | Rank | ID | Produto | Similaridade |
        |---|---|---|---|
        | 1 | 94 | Motor de Popa Volvo Magnum 276HP | 0,8696 |
        | 2 | 11 | GPS Furuno Swift Leviathan Poseidon | 0,8680 |
        | 3 | 35 | Radar Furuno Swift | 0,8539 |
        | 4 | 1 | Transponder AIS Maré Magnum | 0,8500 |
        | 5 | 115 | Cabo de Nylon Delta Force Magnum Leviathan | 0,8500 |
*   **Metodologia:** Matriz binária Usuário x Produto (49x150), similaridade de cosseno, validação cruzada Python vs SQL

---

## Principais Achados

| Dimensão | Resultado |
|---|---|
| Transações com prejuízo | 62,8% (6.213 de 9.895) |
| Prejuízo total identificado | R$ 182,2 milhões |
| Maior prejuízo absoluto | Produto 72 — R$ 39,8 milhões |
| Ticket médio — clientes elite | R$ 290.063 a R$ 336.859 |
| Categoria líder — elite | Propulsão (6.030 itens) |
| Pior dia de vendas | Domingo — R$ 3.229.614,16 |
| Melhor dia de vendas | Sexta-feira — R$ 3.776.151,25 |
| MAE do modelo baseline | 0,9958 unidades/dia |
| Produto mais similar ao GPS | Motor Volvo Magnum 276HP (0,8696) |

---

## Dashboard Interativo

O projeto inclui um dashboard em Streamlit com 6 seções:

*   **Visão Geral** — KPIs, tendência de vendas, top produtos
*   **Prejuízo por Produto (Q04)** — ranking e simulador de impacto
*   **Clientes Elite (Q05)** — top 10 e categorias preferidas
*   **Sazonalidade (Q06)** — média por dia da semana com linha de referência
*   **Previsão de Demanda (Q07)** — gráfico real vs previsto
*   **Recomendação (Q08)** — top 5 produtos similares ao GPS

Para executar: `streamlit run streamlit_app.py`

---

## Validação Cruzada (Python vs SQL)

Todas as análises principais foram implementadas em Python e validadas via SQL com DuckDB, garantindo consistência e auditabilidade dos resultados.

---

## Stack Técnico

| Biblioteca | Papel |
|---|---|
| pandas | Manipulação de dados |
| numpy | Operações numéricas |
| duckdb | SQL sobre DataFrames — validação cruzada |
| requests | API BCB/PTAX para câmbio |
| scikit-learn | Similaridade de cosseno |
| matplotlib / seaborn | Visualizações |
| streamlit | Dashboard interativo |
