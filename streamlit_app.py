# =============================================================================
# LH Nautical - Dashboard de Análise de Dados Aprimorado (Refatorado e Corrigido)
# Desafio Lighthouse - Análise Estratégica de Dados
# =============================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# --- Configuração da Página ---
st.set_page_config(
    page_title="LH Nautical - Dashboard Aprimorado",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Cores da Marca ---
COLORS = {
    'primary': '#007BFF',
    'secondary': '#28A745',
    'danger': '#DC3545',
    'warning': '#FFC107',
    'info': '#17A2B8',
    'text_dark': '#343A40',
    'text_light': '#F8F9FA',
    'background': '#FFFFFF',
    'card_background': '#F8F9FA'
}

# --- Funções de Carga de Dados ---
@st.cache_data
def safe_load_data(file_name, default_cols=None, date_cols_candidates=None):
    """Carrega CSV com cache, verifica existência e retorna DataFrame vazio se não encontrado."""
    path_in_root = file_name
    path_in_outputs = os.path.join('outputs', file_name)

    file_to_load = None
    if os.path.exists(path_in_root):
        file_to_load = path_in_root
    elif os.path.exists(path_in_outputs):
        file_to_load = path_in_outputs

    if file_to_load is None:
        st.warning(f"Arquivo '{file_name}' não encontrado.")
        if default_cols:
            return pd.DataFrame(columns=default_cols)
        return pd.DataFrame()

    try:
        df = pd.read_csv(file_to_load)
        if date_cols_candidates:
            found_date_col = next((col for col in df.columns if col in date_cols_candidates), None)
            if found_date_col:
                df[found_date_col] = pd.to_datetime(df[found_date_col], errors='coerce', dayfirst=True)
                if found_date_col != 'data_venda_clean':
                    df = df.rename(columns={found_date_col: 'data_venda_clean'})
        return df
    except Exception as e:
        st.error(f"Erro ao carregar '{file_name}': {e}")
        if default_cols:
            return pd.DataFrame(columns=default_cols)
        return pd.DataFrame()

@st.cache_data
def load_products_names(file_name='produtos_raw.csv'):
    """Carrega nomes de produtos para mapeamento."""
    df_produtos = safe_load_data(file_name, default_cols=['code', 'name'])
    if not df_produtos.empty and 'code' in df_produtos.columns and 'name' in df_produtos.columns:
        df_produtos_clean = df_produtos.drop_duplicates(subset=['code'])
        return df_produtos_clean.set_index('code')['name'].to_dict()
    return {}

# --- Carregar Todos os Dados ---
st.sidebar.title("⚓ LH Nautical")
st.sidebar.markdown("### Análise Estratégica de Dados")
st.sidebar.markdown("---")

df_vendas = safe_load_data('vendas_2023_2024.csv', default_cols=['id', 'id_client', 'id_product', 'qtd', 'total', 'sale_date'], date_cols_candidates=['sale_date', 'data_venda'])
df_prejuizo = safe_load_data('prejuizo_agregado.csv', default_cols=['id_product', 'prejuizo_total', 'valor_venda', 'percentual_perda'])
df_clientes = safe_load_data('clientes_elite.csv', default_cols=['id_client', 'faturamento_total', 'frequencia', 'diversidade_categorias', 'ticket_medio'])
df_categorias_elite = safe_load_data('categorias_elite.csv', default_cols=['category_normalized', 'total_itens', 'total_vendas'])
df_media_semana = safe_load_data('media_vendas_dia_semana.csv', default_cols=['dia_semana', 'media_vendas'])
df_previsao = safe_load_data('previsao_demanda.csv', default_cols=['data', 'real', 'previsao'], date_cols_candidates=['data'])
df_similares = safe_load_data('produtos_similares.csv', default_cols=['id_product', 'similaridade'])
products_names = load_products_names()

# Processamento do df_vendas
if not df_vendas.empty and 'sale_date' in df_vendas.columns:
    df_vendas['data_venda_clean'] = pd.to_datetime(df_vendas['sale_date'], errors='coerce', dayfirst=True)
    df_vendas = df_vendas.dropna(subset=['data_venda_clean'])
    df_vendas['mes_ano'] = df_vendas['data_venda_clean'].dt.to_period('M').astype(str)

# --- Funções de Renderização de Seções ---

def render_overview_section(df_vendas_data, products_names_data):
    st.title("📊 Visão Geral do Desempenho de Vendas")
    st.markdown("Esta seção oferece um panorama geral das vendas, destacando tendências e os produtos mais vendidos.")
    st.markdown("---")

    if df_vendas_data.empty:
        st.info("Nenhum dado de vendas encontrado. Verifique o arquivo 'vendas_2023_2024.csv'.")
        return pd.DataFrame()

    # Filtro de Data Global para a Visão Geral
    st.sidebar.markdown("### Filtro de Período")
    min_date_available = df_vendas_data['data_venda_clean'].min()
    max_date_available = df_vendas_data['data_venda_clean'].max()

    if pd.isna(min_date_available) or pd.isna(max_date_available):
        st.sidebar.warning("Datas inválidas no DataFrame de vendas. O filtro de data não está disponível.")
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2024, 12, 31)
    else:
        start_date_default = max_date_available - timedelta(days=365) if max_date_available - timedelta(days=365) > min_date_available else min_date_available
        start_date, end_date = st.sidebar.slider(
            "Selecione o período:",
            min_value=min_date_available.to_pydatetime(),
            max_value=max_date_available.to_pydatetime(),
            value=(start_date_default.to_pydatetime(), max_date_available.to_pydatetime()),
            format="YYYY-MM-DD"
        )

    df_vendas_filtered = df_vendas_data[
        (df_vendas_data['data_venda_clean'] >= start_date) &
        (df_vendas_data['data_venda_clean'] <= end_date)
    ].copy()

    if df_vendas_filtered.empty:
        st.warning("Nenhum dado de vendas para o período selecionado.")
        return df_vendas_filtered

    # KPIs
    total_vendas = df_vendas_filtered['total'].sum()
    total_itens_vendidos = df_vendas_filtered['qtd'].sum()
    num_transacoes = df_vendas_filtered.shape[0]
    ticket_medio = total_vendas / num_transacoes if num_transacoes > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Vendas Totais (R$)", f"R$ {total_vendas:,.2f}")
    with col2:
        st.metric("Itens Vendidos", f"{total_itens_vendidos:,.0f}")
    with col3:
        st.metric("Nº Transações", f"{num_transacoes:,.0f}")
    with col4:
        st.metric("Ticket Médio (R$)", f"R$ {ticket_medio:,.2f}")

    st.markdown("---")

    # Gráfico de Tendência de Vendas Diárias
    st.subheader("Tendência de Vendas ao Longo do Tempo")
    vendas_por_dia = df_vendas_filtered.groupby(df_vendas_filtered['data_venda_clean'].dt.to_period('D'))['total'].sum().reset_index()
    vendas_por_dia['data_venda_clean'] = vendas_por_dia['data_venda_clean'].dt.to_timestamp()

    fig_tendencia = px.line(
        vendas_por_dia,
        x='data_venda_clean',
        y='total',
        title='Vendas Diárias ao Longo do Período',
        labels={'data_venda_clean': 'Data', 'total': 'Vendas Totais (R$)'},
        color_discrete_sequence=[COLORS['primary']]
    )
    fig_tendencia.update_layout(hovermode="x unified")
    st.plotly_chart(fig_tendencia, use_container_width=True)

    st.markdown("---")

    # Top 10 Produtos Mais Vendidos
    st.subheader("Top 10 Produtos Mais Vendidos (por Quantidade)")
    if not df_vendas_filtered.empty:
        top_produtos = df_vendas_filtered.groupby('id_product')['qtd'].sum().nlargest(10).reset_index()
        top_produtos['nome_produto'] = top_produtos['id_product'].map(products_names_data).fillna('Desconhecido')
        top_produtos['label'] = top_produtos['id_product'].astype(str) + ' - ' + top_produtos['nome_produto']

        fig_top_produtos = px.bar(
            top_produtos.sort_values('qtd', ascending=True),
            x='qtd',
            y='label',
            orientation='h',
            title='Produtos com Maior Volume de Vendas',
            labels={'qtd': 'Quantidade Vendida', 'label': 'Produto (ID - Nome)'},
            color='qtd',
            color_continuous_scale=px.colors.sequential.Blues
        )
        fig_top_produtos.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_top_produtos, use_container_width=True)
    else:
        st.info("Nenhum produto vendido no período selecionado.")

    st.markdown("---")
    st.info("💡 **Recomendação de Negócio:** Monitore de perto os produtos de alta demanda para garantir estoque adequado e explore oportunidades de cross-selling com base nos padrões de compra.")

    return df_vendas_filtered

def render_prejuizo_section(df_prejuizo_data, products_names_data):
    st.title("📉 Análise de Prejuízo por Produto (Q04)")
    st.markdown("Esta seção identifica os produtos que geram maior prejuízo financeiro para a LH Nautical, tanto em valor absoluto quanto percentual.")
    st.markdown("---")

    if df_prejuizo_data.empty:
        st.info("Para esta seção, execute a Questão 4 para gerar o arquivo 'prejuizo_agregado.csv'.")
        return

    df_prejuizo_plot = df_prejuizo_data.copy()
    df_prejuizo_plot['nome_produto'] = df_prejuizo_plot['id_product'].map(products_names_data).fillna('Desconhecido')
    df_prejuizo_plot['label'] = df_prejuizo_plot['id_product'].astype(str) + ' - ' + df_prejuizo_plot['nome_produto']

    total_prejuizo = df_prejuizo_plot['prejuizo_total'].sum()
    total_receita_afetada = df_prejuizo_plot['valor_venda'].sum()
    percentual_total_perda = (total_prejuizo / total_receita_afetada * 100) if total_receita_afetada > 0 else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Prejuízo Total (R$)", f"R$ {total_prejuizo:,.2f}", delta_color="inverse")
    with col2:
        st.metric("Receita Afetada (R$)", f"R$ {total_receita_afetada:,.2f}")
    with col3:
        st.metric("Percentual de Perda Total", f"{percentual_total_perda:,.2f}%", delta_color="inverse")

    st.markdown("---")

    st.subheader("Top 10 Produtos com Maior Prejuízo Absoluto")
    fig_prejuizo = px.bar(
        df_prejuizo_plot.nlargest(10, 'prejuizo_total').sort_values('prejuizo_total', ascending=True),
        x='prejuizo_total',
        y='label',
        orientation='h',
        title='Produtos com Maior Prejuízo Total',
        labels={'prejuizo_total': 'Prejuízo Total (R$)', 'label': 'Produto (ID - Nome)'},
        color='prejuizo_total',
        color_continuous_scale=px.colors.sequential.Reds,
        hover_data={'prejuizo_total': ':.2f', 'valor_venda': ':.2f', 'percentual_perda': ':.2f'}
    )
    fig_prejuizo.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_prejuizo, use_container_width=True)

    st.markdown("---")

    st.subheader("Top 10 Produtos com Maior Percentual de Perda")
    df_pct_perda_valid = df_prejuizo_plot[df_prejuizo_plot['valor_venda'] > 0].copy()
    fig_pct_perda = px.bar(
        df_pct_perda_valid.nlargest(10, 'percentual_perda').sort_values('percentual_perda', ascending=True),
        x='percentual_perda',
        y='label',
        orientation='h',
        title='Produtos com Maior Percentual de Perda',
        labels={'percentual_perda': 'Percentual de Perda (%)', 'label': 'Produto (ID - Nome)'},
        color='percentual_perda',
        color_continuous_scale=px.colors.sequential.Oranges,
        hover_data={'prejuizo_total': ':.2f', 'valor_venda': ':.2f', 'percentual_perda': ':.2f'}
    )
    fig_pct_perda.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_pct_perda, use_container_width=True)

    st.markdown("---")
    st.info("💡 **Recomendação de Negócio:** Investigue as causas do prejuízo para esses produtos (custo de aquisição, preço de venda, câmbio). Considere ajustar preços, negociar com fornecedores ou descontinuar produtos consistentemente deficitários.")

def render_clientes_elite_section(df_clientes_data, df_categorias_elite_data):
    st.title("👑 Clientes Elite e Suas Preferências (Q05)")
    st.markdown("Esta seção identifica os clientes mais valiosos da LH Nautical e suas categorias de produtos preferidas, auxiliando em estratégias de fidelização e marketing direcionado.")
    st.markdown("---")

    if df_clientes_data.empty:
        st.info("Para esta seção, execute a Questão 5 para gerar o arquivo 'clientes_elite.csv'.")
        return
    if df_categorias_elite_data.empty:
        st.info("Para esta seção, execute a Questão 5 para gerar o arquivo 'categorias_elite.csv'.")
        return

    st.subheader("Top 10 Clientes Fiéis (Elite)")
    df_top_clientes = df_clientes_data.sort_values(by='faturamento_total', ascending=False).head(10).copy()
    df_top_clientes['id_client_label'] = 'Cliente ' + df_top_clientes['id_client'].astype(str)

    fig_clientes_elite = px.bar(
        df_top_clientes.sort_values('faturamento_total', ascending=True),
        x='faturamento_total',
        y='id_client_label',
        orientation='h',
        title='Faturamento Total dos Top 10 Clientes Elite',
        labels={'faturamento_total': 'Faturamento Total (R$)', 'id_client_label': 'Cliente'},
        color='faturamento_total',
        color_continuous_scale=px.colors.sequential.Viridis,
        hover_data={'faturamento_total': ':.2f', 'frequencia': True, 'diversidade_categorias': True, 'ticket_medio': ':.2f'}
    )
    fig_clientes_elite.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_clientes_elite, use_container_width=True)

    st.markdown("#### Detalhes dos Clientes Elite")
    df_display_clientes = df_top_clientes[['id_client', 'faturamento_total', 'frequencia', 'diversidade_categorias', 'ticket_medio']].copy()
    df_display_clientes['faturamento_total'] = df_display_clientes['faturamento_total'].map('R$ {:,.2f}'.format)
    df_display_clientes['ticket_medio'] = df_display_clientes['ticket_medio'].map('R$ {:,.2f}'.format)
    df_display_clientes.rename(columns={
        'id_client': 'ID Cliente',
        'faturamento_total': 'Faturamento Total',
        'frequencia': 'Frequência (Compras)',
        'diversidade_categorias': 'Diversidade Categorias',
        'ticket_medio': 'Ticket Médio'
    }, inplace=True)
    st.dataframe(df_display_clientes, use_container_width=True)

    st.markdown("---")

    st.subheader("Categorias Mais Compradas pelos Clientes Elite")
    df_categorias_elite_plot = df_categorias_elite_data.sort_values(by='total_itens', ascending=False).head(5).copy()

    fig_categorias_elite = px.bar(
        df_categorias_elite_plot.sort_values('total_itens', ascending=True),
        x='total_itens',
        y='category_normalized',
        orientation='h',
        title='Top 5 Categorias Compradas pelos Clientes Elite',
        labels={'total_itens': 'Total de Itens Vendidos', 'category_normalized': 'Categoria'},
        color='total_itens',
        color_continuous_scale=px.colors.sequential.Greens,
        hover_data={'total_itens': True, 'total_vendas': ':.2f'}
    )
    fig_categorias_elite.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_categorias_elite, use_container_width=True)

    st.markdown("---")
    st.info("💡 **Recomendação de Negócio:** Crie programas de fidelidade exclusivos para clientes elite, oferecendo acesso antecipado a novos produtos ou descontos em suas categorias preferidas. Utilize a diversidade de categorias para sugerir produtos complementares.")

def render_sazonalidade_section(df_media_semana_data, df_vendas_data_filtered):
    st.title("🗓️ Análise de Sazonalidade (Q06)")
    st.markdown("Esta seção explora padrões de vendas ao longo da semana e do ano, ajudando a otimizar o planejamento de estoque e campanhas de marketing.")
    st.markdown("---")

    if df_media_semana_data.empty:
        st.info("Para esta seção, execute a Questão 6 para gerar o arquivo 'media_vendas_dia_semana.csv'.")
        return

    st.subheader("Média de Vendas por Dia da Semana")
    order_dias_semana = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
    df_media_semana_data['dia_semana'] = pd.Categorical(df_media_semana_data['dia_semana'], categories=order_dias_semana, ordered=True)

    media_geral_vendas_dia = df_media_semana_data['media_vendas'].mean()

    fig_dia_semana = px.bar(
        df_media_semana_data.sort_values('dia_semana'),
        x='dia_semana',
        y='media_vendas',
        title='Média de Vendas por Dia da Semana',
        labels={'dia_semana': 'Dia da Semana', 'media_vendas': 'Média de Vendas (R$)'},
        color='media_vendas',
        color_continuous_scale=px.colors.sequential.Tealgrn,
        hover_data={'media_vendas': ':.2f'}
    )
    fig_dia_semana.add_hline(y=media_geral_vendas_dia, line_dash="dot", line_color="red",
                             annotation_text=f"Média Geral: R$ {media_geral_vendas_dia:,.2f}",
                             annotation_position="top right")
    st.plotly_chart(fig_dia_semana, use_container_width=True)

    st.markdown("---")

    st.subheader("Tendência de Vendas Mensais")
    if df_vendas_data_filtered.empty:
        st.info("Nenhum dado de vendas filtrado para analisar a tendência mensal. Verifique o filtro de data na Visão Geral.")
        return

    vendas_por_mes = df_vendas_data_filtered.groupby(df_vendas_data_filtered['data_venda_clean'].dt.to_period('M'))['total'].sum().reset_index()
    vendas_por_mes['data_venda_clean'] = vendas_por_mes['data_venda_clean'].dt.to_timestamp()

    fig_tendencia_mensal = px.line(
        vendas_por_mes,
        x='data_venda_clean',
        y='total',
        title='Tendência de Vendas Mensais',
        labels={'data_venda_clean': 'Mês', 'total': 'Vendas Totais (R$)'},
        color_discrete_sequence=[COLORS['info']]
    )
    fig_tendencia_mensal.update_layout(hovermode="x unified")
    st.plotly_chart(fig_tendencia_mensal, use_container_width=True)

    st.markdown("---")
    st.info("💡 **Recomendação de Negócio:** Ajuste a alocação de pessoal e o estoque com base nos dias de maior e menor movimento. Planeje campanhas promocionais para períodos de baixa sazonalidade para estimular as vendas.")

def render_previsao_demanda_section(df_previsao_data, products_names_data):
    import matplotlib.pyplot as plt
    import pandas as pd
    
    st.title("🔮 Previsão de Demanda (Q07)")
    st.markdown("Esta seção apresenta a previsão de demanda para um produto específico, permitindo um planejamento de estoque mais eficiente.")
    st.markdown("---")

    # FORÇAR LEITURA DIRETA DO ARQUIVO CORRETO (janeiro/2024)
    df = None
    for path in ['previsao_demanda.csv', 'outputs/previsao_demanda.csv']:
        try:
            df_temp = pd.read_csv(path)
            if 'data' in df_temp.columns and len(df_temp) >= 20:
                df = df_temp
                st.success(f"✅ Dados carregados: {len(df)} dias (janeiro/2024)")
                break
        except:
            pass
    
    if df is None:
        df = df_previsao_data.copy()
        if df.empty:
            st.info("Execute a Questão 7 para gerar o arquivo 'previsao_demanda.csv'.")
            return
        st.info(f"📊 Dados carregados: {len(df)} registros")
    
    # Identificar coluna de data
    if 'data' in df.columns:
        date_col = 'data'
    elif 'data_venda_clean' in df.columns:
        date_col = 'data_venda_clean'
    else:
        st.error(f"Coluna de data não encontrada. Colunas: {df.columns.tolist()}")
        return
    
    # Preparar dados
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col])
    df = df.sort_values(date_col)

    if df.empty:
        st.warning("Nenhum dado válido.")
        return

    # =============================================================
    # TÍTULO E CONTEXTO
    # =============================================================
    produto_nome = "Motor de Popa Yamaha Evo Dash 155HP"
    st.subheader(f"📈 Previsão de Demanda: {produto_nome}")
    
    st.markdown(f"""
    **Contexto da análise:**
    - **Período de previsão:** {df[date_col].min().strftime('%d/%m/%Y')} a {df[date_col].max().strftime('%d/%m/%Y')}
    - **Modelo utilizado:** Média Móvel Simples com janela de 7 dias
    - **Produto:** Motor de Popa Yamaha Evo Dash 155HP (produto de alta demanda sazonal)
    
    O gráfico abaixo compara as **vendas reais** (linha verde) com a **previsão gerada pelo modelo** (linha laranja tracejada).
    """)
    
    # =============================================================
    # GRÁFICO
    # =============================================================
    mae = (df['real'] - df['previsao']).abs().mean()
    
    fig, ax = plt.subplots(figsize=(12, 5))
    
    ax.plot(df[date_col], df['real'], 
            color='#1D9E75', linewidth=2, marker='o', markersize=4, label='Vendas Reais')
    ax.plot(df[date_col], df['previsao'], 
            color='#D85A30', linewidth=2, linestyle='--', marker='s', markersize=4, label='Previsão (Média Móvel 7 dias)')
    
    ax.set_xlabel('Data', fontsize=12)
    ax.set_ylabel('Quantidade Vendida', fontsize=12)
    ax.set_title(f'Previsão de Demanda — {produto_nome}\nJaneiro 2024 | MAE = {mae:.2f}', fontsize=14)
    
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=30)
    plt.tight_layout()
    
    st.pyplot(fig)
    
    # =============================================================
    # MÉTRICAS DE PERFORMANCE
    # =============================================================
    st.markdown("---")
    st.subheader("📊 Avaliação do Modelo")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("MAE (Erro Absoluto Médio)", f"{mae:.2f} unidades", 
                  help="Mean Absolute Error - média dos erros absolutos entre previsão e real")
    with col2:
        total_vendas = df['real'].sum()
        st.metric("Total de Vendas (jan/2024)", f"{total_vendas:.0f} unidades")
    with col3:
        dias_com_venda = (df['real'] > 0).sum()
        st.metric("Dias com Venda", f"{dias_com_venda} de {len(df)} dias")
    
    # =============================================================
    # ANÁLISE DOS RESULTADOS
    # =============================================================
    st.markdown("---")
    st.subheader("🔍 Análise dos Resultados")
    
    if total_vendas > 0:
        st.markdown(f"""
        **Padrão de Demanda Identificado:**
        - As vendas ocorreram apenas nos dias **21 e 22 de janeiro** (11 e 6 unidades)
        - Os demais {len(df) - dias_com_venda} dias do mês tiveram **vendas zero**
        - Este padrão caracteriza uma **demanda intermitente** (vendas esporádicas)
        
        **Performance do Modelo:**
        - O MAE de **{mae:.2f}** indica que o erro médio das previsões é baixo
        - Porém, o modelo previu zero na maioria dos dias, o que é correto dado o histórico
        - A previsão para os dias 22-28 (2.43 unidades) reflete a média dos dias com vendas
        """)
    else:
        st.info("Nenhuma venda registrada no período analisado.")
    
    # =============================================================
    # RECOMENDAÇÕES DE NEGÓCIO
    # =============================================================
    st.markdown("---")
    st.subheader("💡 Recomendações de Negócio")
    
    st.markdown(f"""
    **Para Produtos com Demanda Intermitente:**
    
    1. **Piso de Segurança:** Considere implementar uma previsão mínima (ex: 1 unidade) para evitar ruptura de estoque em picos inesperados.
    
    2. **Modelos Alternativos:** Avaliar modelos específicos para demanda intermitente, como:
       - **Croston:** Projetado para séries com muitos zeros
       - **Prophet:** Captura sazonalidade e tendências
    
    3. **Gestão de Estoque:** Manter um estoque de segurança reduzido para este produto, considerando que as vendas são esporádicas.
    
    4. **Próximos Passos:** Expandir a previsão para outros produtos de alta rotatividade e comparar a performance do modelo com outros métodos.
    """)
    
    # =============================================================
    # TABELA DE DADOS
    # =============================================================
    with st.expander("📋 Ver dados diários completos"):
        df_display = df[[date_col, 'real', 'previsao']].copy()
        df_display[date_col] = df_display[date_col].dt.strftime('%d/%m/%Y')
        df_display.columns = ['Data', 'Vendas Reais', 'Previsão']
        
        def highlight_vendas(val):
            if isinstance(val, (int, float)) and val > 0:
                return 'background-color: #90EE90'
            return ''
        
        st.dataframe(
            df_display.style.format({
                'Vendas Reais': '{:.0f}',
                'Previsão': '{:.2f}'
            }).applymap(highlight_vendas, subset=['Vendas Reais']),
            use_container_width=True,
            hide_index=True
        )
    
    # =============================================================
    # NOTA METODOLÓGICA
    # =============================================================
    with st.expander("📖 Entenda a Metodologia"):
        st.markdown("""
        ### Como a Previsão foi Calculada?
        
        **Modelo:** Média Móvel Simples (SMA) com janela de 7 dias
        
        **Fórmula:** Para cada dia t, a previsão é a média das vendas dos 7 dias anteriores:
        
        `Previsão(t) = (Vendas[t-1] + Vendas[t-2] + ... + Vendas[t-7]) / 7`
        
        **Prevenção de Data Leakage:**
        - Apenas dados anteriores à data prevista são utilizados
        - Filtro: serie_completa.index < data
        - Validação cruzada Python vs SQL garante a consistência
        
        **Por que a Previsão é Zero na Maior Parte do Mês?**
        
        | Período | Vendas Reais | Previsão | Motivo |
        |---------|--------------|----------|--------|
        | 01/01 a 20/01 | 0 | 0 | Média dos 7 dias anteriores = 0 |
        | 21/01 | 11 | 0 | Média dos dias 14-20 = 0 |
        | 22/01 | 6 | 1,57 | Média dos dias 15-21 = 11/7 = 1,57 |
        | 23/01 a 28/01 | 0 | 2,43 | Média dos dias com venda recente |
        | 29/01 a 31/01 | 0 | 0,86 → 0 | Média cai à medida que os dias de venda saem da janela |
        
        **Limitações do Modelo:**
        - Não captura sazonalidade semanal
        - Subestima picos de demanda esporádicos
        - Para produtos com demanda intermitente, tende a prever zero na maioria dos dias
        """)

def render_recomendacao_section(df_similares_data, products_names_data):
    st.title("🎯 Sistema de Recomendação (Q08)")
    st.markdown("Esta seção apresenta produtos similares, com base no comportamento de compra dos clientes, para auxiliar em estratégias de cross-selling e up-selling.")
    st.markdown("---")

    if df_similares_data.empty:
        st.info("Para esta seção, execute a Questão 8 para gerar o arquivo 'produtos_similares.csv'.")
        return

    st.subheader("Produtos Mais Similares ao GPS Garmin Vortex Maré Drift")

    if not df_similares_data.empty:
        df_similares_plot = df_similares_data.copy()
        df_similares_plot['nome_produto'] = df_similares_plot['id_product'].map(products_names_data).fillna('Desconhecido')
        df_similares_plot['label'] = df_similares_plot['id_product'].astype(str) + ' - ' + df_similares_plot['nome_produto']

        fig_similares = px.bar(
            df_similares_plot.sort_values('similaridade', ascending=True).head(5),
            x='similaridade',
            y='label',
            orientation='h',
            title='Top 5 Produtos Mais Similares ao GPS Garmin Vortex Maré Drift',
            labels={'similaridade': 'Similaridade de Cosseno', 'label': 'Produto (ID - Nome)'},
            color='similaridade',
            color_continuous_scale=px.colors.sequential.Greens,
            range_x=[df_similares_plot['similaridade'].min() * 0.95, df_similares_plot['similaridade'].max() * 1.05],
            hover_data={'similaridade': ':.4f'}
        )
        fig_similares.update_layout(yaxis={'categoryorder':'total ascending'})
        fig_similares.update_traces(hovertemplate='Produto: %{y}<br>Similaridade: %{x:,.4f}')
        st.plotly_chart(fig_similares, use_container_width=True)

        st.markdown("---")
        st.subheader("Ranking Completo de Similaridade")

        df_display_similares = df_similares_plot.copy()
        df_display_similares['destaque'] = ['🥇' if i == 0 else '🥈' if i == 1 else '🥉' if i == 2 else '' for i in range(len(df_display_similares))]

        st.dataframe(df_display_similares[['destaque', 'id_product', 'nome_produto', 'similaridade']], use_container_width=True)

        st.markdown("---")
        st.info("💡 **Recomendação de Negócio:** Implementar uma vitrine de 'Quem comprou isso, também levou...' no site, sugerindo os produtos mais similares ao item que o cliente está visualizando ou acabou de comprar. Por exemplo, para o GPS Garmin Vortex Maré Drift, o produto mais similar é o **Motor de Popa Volvo Magnum 276HP**.")

        with st.expander("Entenda o Sistema de Recomendação"):
            st.markdown("""
            Este sistema de recomendação é baseado na **similaridade de cosseno** entre produtos, calculada a partir do comportamento de compra dos clientes.
            Uma matriz Usuário x Produto é construída, onde 1 indica que o cliente comprou o produto e 0 caso contrário.
            A similaridade de cosseno mede o ângulo entre os vetores de compra de dois produtos; quanto menor o ângulo (mais próximo de 1), mais similares são os produtos em termos de padrões de compra.
            """)
            st.markdown("Para mais detalhes sobre a construção da matriz e as limitações do método, consulte a documentação da Questão 8.3.")

    else:
        st.info("Nenhum dado de similaridade encontrado. Verifique a execução da Questão 8.")

# --- Menu Lateral e Renderização ---
st.sidebar.markdown("### Navegação")
selected_section = st.sidebar.radio(
    "Ir para a seção:",
    [
        "Visão Geral",
        "Análise de Prejuízo (Q04)",
        "Clientes Elite (Q05)",
        "Análise de Sazonalidade (Q06)",
        "Previsão de Demanda (Q07)",
        "Sistema de Recomendação (Q08)"
    ]
)

df_vendas_para_outras_secoes = df_vendas.copy()

if selected_section == "Visão Geral":
    df_vendas_para_outras_secoes = render_overview_section(df_vendas, products_names)
elif selected_section == "Análise de Prejuízo (Q04)":
    render_prejuizo_section(df_prejuizo, products_names)
elif selected_section == "Clientes Elite (Q05)":
    render_clientes_elite_section(df_clientes, df_categorias_elite)
elif selected_section == "Análise de Sazonalidade (Q06)":
    render_sazonalidade_section(df_media_semana, df_vendas_para_outras_secoes)
elif selected_section == "Previsão de Demanda (Q07)":
    render_previsao_demanda_section(df_previsao, products_names)
elif selected_section == "Sistema de Recomendação (Q08)":
    render_recomendacao_section(df_similares, products_names)

# --- Rodapé ---
st.markdown("---")
st.markdown(f"""
*Dashboard desenvolvido para o Desafio Lighthouse - LH Nautical por Patrick* |
[Repositório GitHub](https://github.com/[SEU_USUARIO]/[SEU_REPOSITORIO])
""")