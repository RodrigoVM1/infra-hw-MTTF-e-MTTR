import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página do Streamlit
st.set_page_config(page_title="Métricas de Manutenção (MTTF & MTTR)", layout="wide")

st.title("📊 Calculadora e Painel de MTTF e MTTR")
st.markdown("""
Faça o upload do seu arquivo CSV com os dados de parada e retorno para calcular as métricas e visualizar os gráficos de comportamento do ativo.
""")

# Componente de Upload do arquivo
uploaded_file = st.file_uploader("Escolha um arquivo CSV", type=["csv"])

if uploaded_file is not None:
    try:
        # Lendo o CSV
        df = pd.read_csv(uploaded_file)
        
        # Seleção das colunas por parte do usuário na barra lateral
        st.sidebar.header("🔧 Mapeamento de Colunas")
        col_falha = st.sidebar.selectbox("Coluna da Data/Hora da Falha:", df.columns)
        col_reparo = st.sidebar.selectbox("Coluna da Data/Hora do Retorno:", df.columns)
        
        # Converter colunas para datetime
        df[col_falha] = pd.to_datetime(df[col_falha])
        df[col_reparo] = pd.to_datetime(df[col_reparo])
        
        # Ordenar os dados cronologicamente
        df = df.sort_values(by=col_falha).reset_index(drop=True)
        
        # --- CÁLCULOS ---
        # 1. Tempo de Reparo (Downtime)
        df['Tempo_Reparo_Horas'] = (df[col_reparo] - df[col_falha]).dt.total_seconds() / 3600
        
        # 2. Tempo Entre Falhas (Uptime)
        df['Tempo_Funcionamento_Horas'] = (df[col_falha].shift(-1) - df[col_reparo]).dt.total_seconds() / 3600
        
        # Médias
        mttr = df['Tempo_Reparo_Horas'].mean()
        mttf = df['Tempo_Funcionamento_Horas'].dropna().mean()
        num_falhas = len(df)
        
        # --- EXIBIÇÃO DOS CARDS DE MÉTRICAS ---
        st.divider()
        m1, m2, m3, m4 = st.columns(4)
        
        with m1:
            st.metric(label="MTTF (Tempo Médio de Bom Funcionamento)", value=f"{mttf:.2f} h" if not pd.isna(mttf) else "N/A")
        with m2:
            st.metric(label="MTTR (Tempo Médio de Reparo)", value=f"{mttr:.2f} h" if not pd.isna(mttr) else "N/A")
        with m3:
            st.metric(label="Total de Falhas", value=num_falhas)
        with m4:
            if not pd.isna(mttf) and mttr + mttf > 0:
                disponibilidade = (mttf / (mttf + mttr)) * 100
                st.metric(label="Disponibilidade (Availability)", value=f"{disponibilidade:.2f}%")
            else:
                st.metric(label="Disponibilidade", value="N/A")

        # --- SEÇÃO DE GRÁFICOS ---
        st.divider()
        st.subheader("📈 Linha do Tempo e Histórico do Ativo")
        
        # Criando um dataframe limpo para plotar a evolução temporal
        df_linha_tempo = df.copy()
        df_linha_tempo['Data'] = df_linha_tempo[col_falha].dt.strftime('%Y-%m-%d')
        
        # Gráfico 1: Evolução dos Tempos ao longo do tempo
        fig_timeline = px.line(
            df_linha_tempo, 
            x=col_falha, 
            y=['Tempo_Funcionamento_Horas', 'Tempo_Reparo_Horas'],
            labels={'value': 'Horas', 'variable': 'Métrica', col_falha: 'Linha do Tempo'},
            title="Evolução Temporal dos Tempos de Funcionamento vs. Reparo",
            markers=True
        )
        # Customização de nomes na legenda
        newnames = {'Tempo_Funcionamento_Horas': 'Tempo até a Próxima Falha (Uptime)', 'Tempo_Reparo_Horas': 'Tempo do Reparo (Downtime)'}
        fig_timeline.for_each_trace(lambda t: t.update(name = newnames[t.name]))
        
        st.plotly_chart(fig_timeline, use_container_width=True)
        
        # Gráficos 2 e 3: Distribuição (Lado a Lado)
        st.subheader("📊 Análise de Distribuição e Frequência")
        g1, g2 = st.columns(2)
        
        with g1:
            fig_hist_mttf = px.histogram(
                df.dropna(subset=['Tempo_Funcionamento_Horas']), 
                x="Tempo_Funcionamento_Horas", 
                nbins=10,
                title="Distribuição do Tempo de Funcionamento (MTTF)",
                color_discrete_sequence=['#2ca02c'],
                labels={'Tempo_Funcionamento_Horas': 'Horas em Funcionamento'}
            )
            fig_hist_mttf.add_vline(x=mttf, line_dash="dash", line_color="black", annotation_text=f"Média (MTTF): {mttf:.1f}h")
            st.plotly_chart(fig_hist_mttf, use_container_width=True)
            
        with g2:
            fig_hist_mttr = px.histogram(
                df, 
                x="Tempo_Reparo_Horas", 
                nbins=10,
                title="Distribuição do Tempo de Reparo (MTTR)",
                color_discrete_sequence=['#d62728'],
                labels={'Tempo_Reparo_Horas': 'Horas em Manutenção'}
            )
            fig_hist_mttr.add_vline(x=mttr, line_dash="dash", line_color="black", annotation_text=f"Média (MTTR): {mttr:.1f}h")
            st.plotly_chart(fig_hist_mttr, use_container_width=True)
            
        # Tabela original para conferência no rodapé
        with st.expander("📄 Ver tabela de dados processados completa"):
            st.dataframe(df)

    except Exception as e:
        st.error(f"Erro ao processar o arquivo ou gerar os gráficos: {e}")
        st.warning("Certifique-se de que as colunas selecionadas contêm datas válidas.")
else:
    st.info("💡 Aguardando o upload do arquivo CSV para gerar os insights e gráficos.")