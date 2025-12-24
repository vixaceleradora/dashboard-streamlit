import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(layout="wide", page_title="Dashboard Vendas - Estúdio Roots")

# URL da planilha
url = 'https://docs.google.com/spreadsheets/d/1FCiwiYfcqABSgepSRU0aZ62EwBTcXnv85TccyFe7d4k/export?format=csv&gid=1702469341'

# Carregar dados
@st.cache_data
def load_data():
    df = pd.read_csv(url)
    
    # Limpeza de dados
    df["Data"] = pd.to_datetime(df["Data"], dayfirst=True, format='%d/%m/%Y')
    
    # Remover linhas com datas inválidas (NaT)
    df = df.dropna(subset=['Data'])
    
    df["Mês"] = df["Data"].dt.to_period("M").astype(str)
    
    # Unificar todas as variações de conversações em "Conversas Iniciadas"
    df['Tipo de resultado'] = df['Tipo de resultado'].str.replace(
        r'onsite_conversion\..*messaging.*', 'onsite_conversion.total_messaging_connection', regex=True
    )
    
    # Mapeamento de tipos de resultado para nomes amigáveis
    tipo_resultado_map = {
        'onsite_conversion.total_messaging_connection': 'Conversas Iniciadas',
        'onsite_conversion.lead': 'Leads Formulário',
        'page_engagement': 'Engajamento',
        'link_click': 'Cliques no Link',
        'offsite_conversion.fb_pixel_purchase': 'Compras',
        'offsite_conversion.fb_pixel_add_to_cart': 'Adicionados ao Carrinho',
        'offsite_conversion.fb_pixel_view_content': 'Visualizações de Conteúdo',
        'offsite_conversion.fb_pixel_lead': 'Leads Formulário',
        'offsite_conversion.fb_pixel_initiate_checkout': 'Início de Compra',
        'post_engagement': 'Engajamento em Post',
        'app_install': 'Instalações de App',
        'app_engagement': 'Engajamento no App',
    }
    
    # Criar coluna com nomes amigáveis
    df['Tipo de Resultado (Legível)'] = df['Tipo de resultado'].map(tipo_resultado_map)
    # Se não encontrar no mapa, usa o valor original
    df['Tipo de Resultado (Legível)'] = df['Tipo de Resultado (Legível)'].fillna(df['Tipo de resultado'])
    
    # Remover "R$ " e converter para float
    colunas_monetarias = ['Valor usado', 'Custo por resultado', 'CPC (no link)', 'CPM', 'CPP']
    for col in colunas_monetarias:
        if col in df.columns:
            df[col] = df[col].str.replace('R$ ', '', regex=False).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df

df = load_data()

# Layout do topo
top_left, top_right = st.columns([4, 1])

with top_left:
    st.title("📊 Dashboard de Vendas - Estúdio Roots")

with top_right:
    meses_opcoes = ['Todos os períodos'] + sorted(df["Mês"].unique(), reverse=True)
    month = st.selectbox("Mês", meses_opcoes, index=1, key="seletor_mes")
    
    tipos_resultado_unicos = sorted([x for x in df["Tipo de Resultado (Legível)"].unique().tolist() if pd.notna(x)])
    
    # Encontrar o índice de "Conversas Iniciadas" se existir
    indice_padrao = 0
    if 'Conversas Iniciadas' in tipos_resultado_unicos:
        indice_padrao = tipos_resultado_unicos.index('Conversas Iniciadas') + 1  # +1 por causa de "Todos"
    
    tipo_resultado_global = st.selectbox(
        "Tipo de Resultado",
        options=['Todos'] + tipos_resultado_unicos,
        index=indice_padrao,
        key="filtro_tipo_resultado_global"
    )

st.caption(f"Período selecionado: **{month}**")

# Filtrar dados pelo mês
if month == 'Todos os períodos':
    df_filtered = df.copy()
else:
    df_filtered = df[df['Mês'] == month].copy()

# Filtrar por tipo de resultado se selecionado
if tipo_resultado_global != 'Todos':
    df_filtered = df_filtered[df_filtered['Tipo de Resultado (Legível)'] == tipo_resultado_global].copy()

if df_filtered.empty:
    st.warning("Nenhum dado disponível para o período selecionado.")
else:
    # ===== SEÇÃO 1: MÉTRICAS RESUMIDAS =====
    st.markdown("""
    <span style="
        background-color:#1f77b4;
        color:white;
        padding:8px 16px;
        border-radius:12px;
        font-size:16px;
        font-weight:600;
    ">
    📌 Resumo de Métricas
    </span>
    """, unsafe_allow_html=True)
    
    st.markdown("")  # Espaçamento
    
    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
    
    with col_m1:
        total_investido = df_filtered['Valor usado'].sum()
        st.metric("Total Investido", f"R$ {total_investido:.2f}")
    
    with col_m2:
        alcance = df_filtered['Alcance'].sum()
        st.metric("Alcance", f"{int(alcance):,}")
    
    with col_m3:
        total_resultados = df_filtered['Resultados'].sum()
        st.metric("Resultados", f"{int(total_resultados):,}")
    
    with col_m4:
        media_custo_resultado = df_filtered['Custo por resultado'].mean()
        st.metric("Custo por Resultado", f"R$ {media_custo_resultado:.2f}")
    
    with col_m5:
        # Taxa de conversão = Resultados / Alcance
        alcance_total = df_filtered['Alcance'].sum()
        resultados_total = df_filtered['Resultados'].sum()
        if alcance_total > 0:
            taxa_conversao = (resultados_total / alcance_total) * 100
        else:
            taxa_conversao = 0
        st.metric("Taxa de Conversão", f"{taxa_conversao:.2f}%")
    
    st.markdown("")  # Espaçamento
    
    # ===== SEÇÃO 2: GRÁFICOS =====
    st.markdown("""
    <span style="
        background-color:#1f77b4;
        color:white;
        padding:8px 16px;
        border-radius:12px;
        font-size:16px;
        font-weight:600;
    ">
    📊 Visualizações
    </span>
    """, unsafe_allow_html=True)
    
    st.markdown("")  # Espaçamento
    
    col1, col2 = st.columns(2)
    
    # Gráfico 1: Investimento por Tipo de Resultado
    with col1:
        fig_resultado = px.pie(
            df_filtered,
            values='Valor usado',
            names='Tipo de Resultado (Legível)',
            title='Distribuição de Investimento por Tipo de Resultado',
            hole=0.4
        )
        fig_resultado.update_traces(textposition='inside', textinfo='label+percent')
        st.plotly_chart(fig_resultado, use_container_width=True)
    
    # Gráfico 2: Evolução Investimento x Resultado
    with col2:
        if tipo_resultado_global == 'Todos':
            # Quando é "Todos", agrupar por data e tipo de resultado
            daily_data = df_filtered.groupby(['Data', 'Tipo de Resultado (Legível)']).agg({
                'Valor usado': 'sum',
                'Resultados': 'sum'
            }).reset_index().sort_values('Data')
            
            fig_evolution = px.bar(
                daily_data,
                x='Data',
                y='Resultados',
                color='Tipo de Resultado (Legível)',
                title='Evolução Investimento x Resultados',
                labels={'Resultados': 'Resultados', 'Data': 'Data'},
                text='Resultados'
            )
            
            fig_evolution.update_traces(textposition='inside', textfont=dict(color='white'))
            
            # Adicionar linha de investimento
            daily_investimento = df_filtered.groupby('Data')['Valor usado'].sum().reset_index().sort_values('Data')
            fig_evolution.add_scatter(
                x=daily_investimento['Data'],
                y=daily_investimento['Valor usado'],
                mode='lines+markers',
                name='Investimento',
                yaxis='y2',
                line=dict(color='red', width=3)
            )
            
            # Configurar eixo Y secundário
            fig_evolution.update_layout(
                yaxis2=dict(
                    title='Investimento (R$)',
                    overlaying='y',
                    side='right'
                ),
                yaxis=dict(range=[0, 100]),
                xaxis=dict(tickformat='%d'),
                hovermode='x unified'
            )
        else:
            # Quando é um tipo específico
            daily_data = df_filtered.groupby('Data').agg({
                'Valor usado': 'sum',
                'Resultados': 'sum'
            }).reset_index().sort_values('Data')
            
            fig_evolution = px.bar(
                daily_data,
                x='Data',
                y='Resultados',
                title='Evolução Investimento x Resultados',
                labels={'Resultados': 'Resultados', 'Data': 'Data'},
                text='Resultados'
            )
            
            fig_evolution.update_traces(textposition='inside', textfont=dict(color='white'))
            
            # Adicionar linha de investimento
            fig_evolution.add_scatter(
                x=daily_data['Data'],
                y=daily_data['Valor usado'],
                mode='lines+markers',
                name='Investimento',
                yaxis='y2',
                line=dict(color='red', width=3)
            )
            
            # Configurar eixo Y secundário
            fig_evolution.update_layout(
                yaxis2=dict(
                    title='Investimento (R$)',
                    overlaying='y',
                    side='right'
                ),
                yaxis=dict(range=[0, 100]),
                xaxis=dict(tickformat='%d'),
                hovermode='x unified'
            )
        
        st.plotly_chart(fig_evolution, use_container_width=True)
    
    st.markdown("")  # Espaçamento
    
    col3, col4 = st.columns(2)
    
    # Gráfico 3: Top 10 Anúncios por Performance
    with col3:
        if tipo_resultado_global == 'Todos':
            # Quando é "Todos", pegar o tipo de resultado de cada anúncio
            top_ads = df_filtered.groupby('Anúncio')[['Valor usado', 'Custo por resultado', 'Tipo de Resultado (Legível)']].agg({
                'Valor usado': 'sum',
                'Custo por resultado': 'mean',
                'Tipo de Resultado (Legível)': 'first'
            }).sort_values('Custo por resultado', ascending=False).head(10).reset_index()
            
            fig_ads = px.bar(
                top_ads,
                x='Custo por resultado',
                y='Anúncio',
                orientation='h',
                color='Tipo de Resultado (Legível)',
                title='Top 10 Anúncios por Performance<br><sub>Melhores anúncios por menor custo por resultado</sub>',
                labels={'Custo por resultado': 'Custo por Resultado (R$)', 'Anúncio': 'Anúncio'}
            )
        else:
            # Quando é um tipo específico, não colorir
            top_ads = df_filtered.groupby('Anúncio')[['Valor usado', 'Custo por resultado']].agg({
                'Valor usado': 'sum',
                'Custo por resultado': 'mean'
            }).sort_values('Custo por resultado', ascending=False).head(10).reset_index()
            
            fig_ads = px.bar(
                top_ads,
                x='Custo por resultado',
                y='Anúncio',
                orientation='h',
                title='Top 10 Anúncios por Performance<br><sub>Melhores anúncios por menor custo por resultado</sub>',
                labels={'Custo por resultado': 'Custo por Resultado (R$)', 'Anúncio': 'Anúncio'}
            )
        
        st.plotly_chart(fig_ads, use_container_width=True)
    
    # Gráfico 4: Custo por Clique (CPC) por Tipo de Resultado
    with col4:
        cpc_data = df_filtered.groupby('Tipo de Resultado (Legível)')['CPC (no link)'].mean().reset_index()
        fig_cpc = px.bar(
            cpc_data,
            x='Tipo de Resultado (Legível)',
            y='CPC (no link)',
            title='CPC Médio por Tipo de Resultado',
            labels={'CPC (no link)': 'CPC Médio (R$)', 'Tipo de Resultado (Legível)': 'Tipo de Resultado'}
        )
        st.plotly_chart(fig_cpc, use_container_width=True)
    
    st.markdown("")  # Espaçamento
    
    # ===== SEÇÃO 3: PERFORMANCE DE ANÚNCIOS =====
    st.markdown("""
    <span style="
        background-color:#1f77b4;
        color:white;
        padding:8px 16px;
        border-radius:12px;
        font-size:16px;
        font-weight:600;
    ">
    📈 Performance de Anúncios
    </span>
    """, unsafe_allow_html=True)
    
    st.markdown("")  # Espaçamento
    
    # Usar o filtro global de tipo de resultado
    tipo_resultado_selecionado = tipo_resultado_global
    
    # df_filtered já está filtrado pelo tipo de resultado global
    df_performance = df_filtered.copy()
    
    # Tabela de Performance
    performance_df = df_performance.groupby(['Anúncio', 'Tipo de Resultado (Legível)']).agg({
        'Resultados': 'sum',
        'Valor usado': 'sum',
        'Custo por resultado': 'mean'
    }).reset_index().sort_values('Resultados', ascending=False)
    
    performance_df.columns = ['Anúncio', 'Ações', 'Resultados', 'Valor usado', 'Custo por resultado']
    
    # Formatar para exibição
    display_df = performance_df.copy()
    display_df['Resultados'] = display_df['Resultados'].astype(int)
    display_df['Valor usado'] = display_df['Valor usado'].apply(lambda x: f"R$ {x:.2f}")
    display_df['Custo por resultado'] = display_df['Custo por resultado'].apply(lambda x: f"R$ {x:.2f}")
    
    # Se o filtro for diferente de "Todos", preencher a coluna Ações com o tipo selecionado
    if tipo_resultado_selecionado != 'Todos':
        display_df['Ações'] = tipo_resultado_selecionado
    else:
        display_df['Ações'] = ''
    
    # Tabela principal
    st.dataframe(
        display_df[['Anúncio', 'Resultados', 'Ações', 'Custo por resultado', 'Valor usado']],
        use_container_width=True,
        hide_index=True,
        height=len(display_df) * 35 + 50,
        column_config={
            'Anúncio': st.column_config.TextColumn(width='medium'),
            'Resultados': st.column_config.TextColumn(width='small'),
            'Ações': st.column_config.TextColumn(width='medium'),
            'Custo por resultado': st.column_config.TextColumn(width='medium'),
            'Valor usado': st.column_config.TextColumn(width='medium')
        }
    )
    
    st.markdown("")  # Espaçamento
    
    # Rodapé com resumo (alinhado com a tabela principal)
    total_resultados = int(performance_df['Resultados'].sum())
    total_valor_usado = performance_df['Valor usado'].sum()
    media_custo = performance_df['Custo por resultado'].mean()
    total_anuncios = len(performance_df)
    
    # Se o filtro for diferente de "Todos", preencher com o tipo selecionado; senão deixar vazio
    acao_rodape = tipo_resultado_selecionado if tipo_resultado_selecionado != 'Todos' else ''
    
    resumo_df = pd.DataFrame({
        'Anúncio': [f'TOTAL ({total_anuncios})'],
        'Resultados': [total_resultados],
        'Ações': [acao_rodape],
        'Custo por resultado': [f"R$ {media_custo:.2f}"],
        'Valor usado': [f"R$ {total_valor_usado:.2f}"]
    })
    
    st.dataframe(
        resumo_df[['Anúncio', 'Resultados', 'Ações', 'Custo por resultado', 'Valor usado']],
        use_container_width=True,
        hide_index=True,
        column_config={
            'Anúncio': st.column_config.TextColumn(width='medium'),
            'Resultados': st.column_config.TextColumn(width='small'),
            'Ações': st.column_config.TextColumn(width='medium'),
            'Custo por resultado': st.column_config.TextColumn(width='medium'),
            'Valor usado': st.column_config.TextColumn(width='medium')
        }
    )