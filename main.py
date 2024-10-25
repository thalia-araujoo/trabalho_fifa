import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Função para carregar dados de múltiplos arquivos
@st.cache_data
def load_data(files):
    dfs = [pd.read_csv(file) for file in files]
    return pd.concat(dfs, ignore_index=True)

# Função para aplicar filtros
def apply_filters(df, position, nationality, age_range, rating_range, league):
    if position != 'All':
        df = df[df['player_positions'].str.contains(position)]
    if nationality != 'All':
        df = df[df['nationality'] == nationality]
    if league != 'All':
        df = df[df['league_name'] == league]
    df = df[(df['age'] >= age_range[0]) & (df['age'] <= age_range[1])]
    df = df[(df['overall'] >= rating_range[0]) & (df['overall'] <= rating_range[1])]
    return df

# Função para plotar comparações
def plot_comparison(data_21, data_22, attribute):
    plt.figure(figsize=(10, 5))
    plt.plot(data_21['age'], data_21[attribute], label='FIFA 21', color='blue')
    plt.plot(data_22['age'], data_22[attribute], label='FIFA 22', color='red')
    plt.title(f'Impacto da Idade em {attribute.capitalize()}')
    plt.xlabel('Idade')
    plt.ylabel(attribute.capitalize())
    plt.legend()
    st.pyplot()

# Título do Dashboard
st.title("⚽ Análise Interativa de Jogadores FIFA 🌟")

# Upload dos Datasets
uploaded_files_21 = st.file_uploader("Escolha os arquivos FIFA 21", type='csv', accept_multiple_files=True)
uploaded_files_22 = st.file_uploader("Escolha os arquivos FIFA 22", type='csv', accept_multiple_files=True)

if uploaded_files_21 and uploaded_files_22:
    df_21 = load_data(uploaded_files_21)
    df_22 = load_data(uploaded_files_22)

    st.subheader("Dados FIFA 21")
    st.write(df_21.head())
    
    st.subheader("Dados FIFA 22")
    st.write(df_22.head())

    # Filtros na barra lateral
    st.sidebar.header("Filtros")

    positions = ['All'] + list(df_21['player_positions'].str.split(',').explode().unique())
    selected_position = st.sidebar.selectbox("Selecione uma posição", positions)

    nationalities = ['All'] + list(df_21['nationality'].unique())
    selected_nationality = st.sidebar.selectbox("Selecione uma nacionalidade", nationalities)

    leagues = ['All'] + list(df_21['league_name'].unique())
    selected_league = st.sidebar.selectbox("Selecione uma liga", leagues)

    age_range = st.sidebar.slider("Selecione a faixa etária", 16, 40, (16, 40))
    rating_range = st.sidebar.slider("Selecione a faixa de rating", 0, 100, (0, 100))

    # Aplicando filtros
    df_21_filtered = apply_filters(df_21, selected_position, selected_nationality, age_range, rating_range, selected_league)
    df_22_filtered = apply_filters(df_22, selected_position, selected_nationality, age_range, rating_range, selected_league)

    # Estatísticas Descritivas
    st.subheader("Estatísticas Descritivas")
    st.write("FIFA 21:")
    st.write(df_21_filtered.describe())
    st.write("FIFA 22:")
    st.write(df_22_filtered.describe())

    # Análise Comparativa
    st.subheader("Comparação entre FIFA 21 e FIFA 22")

    if 'overall' in df_21_filtered.columns and 'overall' in df_22_filtered.columns:
        fig, ax = plt.subplots(1, 2, figsize=(12, 6))
        sns.histplot(df_21_filtered['overall'], kde=True, ax=ax[0], color='blue')
        ax[0].set_title('Distribuição de Ratings FIFA 21')
        ax[0].set_xlabel('Rating')
        ax[0].set_ylabel('Frequência')
        
        sns.histplot(df_22_filtered['overall'], kde=True, ax=ax[1], color='red')
        ax[1].set_title('Distribuição de Ratings FIFA 22')
        ax[1].set_xlabel('Rating')
        ax[1].set_ylabel('Frequência')

        st.pyplot(fig)
    else:
        st.error("A coluna 'overall' não foi encontrada em um dos datasets.")

    # Comparação de ratings médios
    st.subheader("Média de Ratings por Posição")
    avg_ratings_21 = df_21_filtered.groupby('player_positions')['overall'].mean().reset_index()
    avg_ratings_22 = df_22_filtered.groupby('player_positions')['overall'].mean().reset_index()

    comparison_df = pd.merge(avg_ratings_21, avg_ratings_22, on='player_positions', how='outer', suffixes=('_21', '_22')).fillna(0)
    st.bar_chart(comparison_df.set_index('player_positions'))

    # Comparação de Atributos Médios
    st.subheader("Comparação de Atributos Médios")
    attribute_columns = ['pace', 'shooting', 'passing', 'dribbling', 'defending', 'physic']
    avg_attributes_21 = df_21_filtered[attribute_columns].mean()
    avg_attributes_22 = df_22_filtered[attribute_columns].mean()

    attributes_comparison = pd.DataFrame({
        'FIFA 21': avg_attributes_21,
        'FIFA 22': avg_attributes_22
    })
    
    st.bar_chart(attributes_comparison)

    # Análise do Impacto da Idade nos Atributos
    st.subheader("Impacto da Idade nos Atributos")
    df_21_age = df_21_filtered.groupby('age')[attribute_columns].mean().reset_index()
    df_22_age = df_22_filtered.groupby('age')[attribute_columns].mean().reset_index()

    for attribute in attribute_columns:
        plot_comparison(df_21_age, df_22_age, attribute)

    # Comparação entre Ligas
    st.subheader("Comparação de Ratings e Atributos por Liga")
    league_avg = df_21_filtered.groupby('league_name')['overall'].mean().reset_index()
    league_avg['version'] = 'FIFA 21'
    league_avg_22 = df_22_filtered.groupby('league_name')['overall'].mean().reset_index()
    league_avg_22['version'] = 'FIFA 22'

    league_comparison = pd.concat([league_avg, league_avg_22], ignore_index=True)
    
    plt.figure(figsize=(12, 6))
    sns.barplot(data=league_comparison, x='league_name', y='overall', hue='version')
    plt.title('Comparação de Ratings Médios por Liga')
    plt.xticks(rotation=45)
    st.pyplot()

    # Selecionar Jogadores para Comparação
    selected_players = st.sidebar.multiselect("Escolha jogadores para comparar", options=df_21_filtered['short_name'].unique())

    if selected_players:
        player_data_21 = df_21_filtered[df_21_filtered['short_name'].isin(selected_players)]
        player_data_22 = df_22_filtered[df_22_filtered['short_name'].isin(selected_players)]

        # Comparação de Atributos
        comparison_data = pd.DataFrame({
            'Atributo': attribute_columns,
            'FIFA 21': player_data_21[attribute_columns].mean().values.flatten(),
            'FIFA 22': player_data_22[attribute_columns].mean().values.flatten()
        })

        st.subheader("Comparação de Atributos dos Jogadores Selecionados")
        st.bar_chart(comparison_data.set_index('Atributo'))

        # Análise de Valores e Salários
        comparison_value_salary = pd.DataFrame({
            'Jogador': player_data_21['short_name'].values,
            'Valor (EUR)': player_data_21['value_eur'].values,
            'Salário (EUR)': player_data_21['wage_eur'].values,
            'Versão': 'FIFA 21'
        })

        player_data_22_filtered = player_data_22[['short_name', 'value_eur', 'wage_eur']].copy()
        player_data_22_filtered['Versão'] = 'FIFA 22'
        player_data_22_filtered.rename(columns={'short_name': 'Jogador', 'value_eur': 'Valor (EUR)', 'wage_eur': 'Salário (EUR)'}, inplace=True)

        comparison_value_salary = pd.concat([comparison_value_salary, player_data_22_filtered], ignore_index=True)

        # Gráfico de Comparação de Valores e Salários
        st.subheader("Comparação de Valor e Salário dos Jogadores Selecionados")
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.barplot(data=comparison_value_salary.melt(id_vars='Jogador', value_vars=['Valor (EUR)', 'Salário (EUR)'], var_name='Categoria', value_name='Valor'), 
                     x='Jogador', y='Valor', hue='Categoria', ax=ax)
        ax.set_title('Comparação de Valor e Salário')
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
        st.pyplot(fig)

    # Análise de Jogadores Selecionados
    selected_player = st.sidebar.selectbox("Escolha um jogador para detalhes", options=df_21_filtered['short_name'].unique())
    player_data_21 = df_21_filtered[df_21_filtered['short_name'] == selected_player]
    player_data_22 = df_22_filtered[df_22_filtered['short_name'] == selected_player]

    if not player_data_21.empty and not player_data_22.empty:
        st.subheader(f"Dados do Jogador: {selected_player}")
        st.write("FIFA 21:")
        st.write(player_data_21)
        
        st.write("FIFA 22:")
        st.write(player_data_22)
    else:
        st.warning("Jogador não encontrado em um dos datasets.")
