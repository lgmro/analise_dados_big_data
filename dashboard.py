import streamlit as st
import pandas as pd
import altair as alt
import calendar
import plotly.express as px
import json
from urllib.request import urlopen

# source venv/bin/activate
# streamlit run dashboard.py
st.set_page_config(
    page_title="Dashboard Anac",
    page_icon=":airplane:",
    layout="wide",
    initial_sidebar_state="expanded")


DATE_COLUMN = 'date/time'
DATA_CSV = ('Anac_data.csv')
MONTHS_ORDER = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

base = pd.read_csv(DATA_CSV)

with st.sidebar:
    st.title(':airplane: Dashboard Anac')
    anos = base["ANO"].value_counts().index
    ano = st.sidebar.selectbox("Anos", anos)
    # meses = base["MES"].value_counts().index
    # mes = st.sidebar.selectbox("Meses", meses)
    empresas =  base["EMPRESA_SIGLA"].value_counts().index
    empresa = st.sidebar.selectbox("Empresas", empresas)

base_filtrada = base.loc[(base['ANO'] == ano) & (base['EMPRESA_SIGLA'] == empresa)]

# Funções de formatação
def formatar(valor):
    return "{:,.0f}".format(valor)

def formatarPorcentagem(valor):
    return "{:,.0f}%".format(valor)

def human_format(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', ' K', ' M', ' B', ' T'][magnitude])


col = st.columns((1.5, 4.5, 2), gap='medium')
# Donut chart
def make_donut(input_response, input_text, input_color):
  if input_color == 'blue':
      chart_color = ['#29b5e8000080', '#155F7A']
  if input_color == 'green':
      chart_color = ['#27AE60', '#12783D']
  if input_color == 'orange':
      chart_color = ['#F39C12', '#875A12']
  if input_color == 'red':
      chart_color = ['#E74C3C', '#781F16']
  if input_color == 'yellow':
      chart_color = ['#ffff53', '#e9e935']
    
  source = pd.DataFrame({
      "Tópico": ['', input_text],
      "Valor(%)": input_response
  })
  source_bg = pd.DataFrame({
      "Tópico": ['', input_text],
      "Valor(%)": [100, 0]
  })
    
  plot = alt.Chart(source).mark_arc(innerRadius=45, cornerRadius=25).encode(
      theta="Valor(%)",
      color= alt.Color("Tópico:N",
                      scale=alt.Scale(
                          #domain=['A', 'B'],
                          domain=[input_text, ''],
                          # range=['#29b5e8', '#155F7A']),  # 31333F
                          range=chart_color),
                      legend=None),
  ).properties(width=130, height=130)
    
  text = plot.mark_text(align='center', color="#29b5e8", font="Lato", fontSize=32, fontWeight=700, fontStyle="italic").encode(text=alt.value(f'{input_response} %'))
  plot_bg = alt.Chart(source_bg).mark_arc(innerRadius=45, cornerRadius=20).encode(
      theta="Valor(%)",
      color= alt.Color("Tópico:N",
                      scale=alt.Scale(
                          # domain=['A', 'B'],
                          domain=[input_text, ''],
                          range=chart_color),  # 31333F
                      legend=None)
  ).properties(width=130, height=130)
  return plot_bg + plot + text

# Carregar geojson do Brasil
with urlopen('https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson') as response:
    brasil = json.load(response)

# Usar nome do estado completo
state_id_map = {}
for feature in brasil['features']:
 feature['id'] = feature['properties']['name']
 state_id_map[feature['properties']['sigla']] = feature['id']
base_filtrada['AEROPORTO_DE_DESTINO_UF'] = base_filtrada['AEROPORTO_DE_DESTINO_UF'].apply(lambda x: state_id_map[x])

def make_choropleth(data):
    choropleth = px.choropleth(data, geojson = brasil, locations='AEROPORTO_DE_DESTINO_UF', color='DECOLAGENS',
                               range_color = (0, max(data.DECOLAGENS)),
                               hover_name = 'AEROPORTO_DE_DESTINO_UF',
                               hover_data = ['COMBUSTIVEL_LITROS', 'DISTANCIA_VOADA_KM', 'HORAS_VOADAS'],
                               labels = {'AEROPORTO_DE_DESTINO_UF': 'Estado', 'COMBUSTIVEL_LITROS' : 'Combustível', 'DISTANCIA_VOADA_KM' : 'Distância voada', 'HORAS_VOADAS' : 'Horas voadas'}
                              )
    choropleth.update_layout(
        template='plotly_dark',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=350
    )
    choropleth.update_geos(fitbounds = 'locations', visible = False)
    return choropleth

with col[0]:
    # Air Passenger Load Factor
    st.markdown('#### Load Factor')
    valores_rpk_ask = base_filtrada[['EMPRESA_SIGLA', 'RPK', 'ASK']].groupby(['EMPRESA_SIGLA']).sum()
    air_passenger_load_factor = (valores_rpk_ask.RPK/valores_rpk_ask.ASK)*100
    air_passenger_load_factor = air_passenger_load_factor.to_frame()
    air_passenger_load_factor.columns = ['AIR_PASSENGER_LOAD_FACTOR']
    air_passenger_load_factor['AIR_PASSENGER_LOAD_FACTOR'] = air_passenger_load_factor['AIR_PASSENGER_LOAD_FACTOR'].apply(formatar)
    valor_air_passenger = air_passenger_load_factor.iat[0,0]
    air_passenger_chart = make_donut(valor_air_passenger, 'Air Passenger', 'yellow')
    st.altair_chart(air_passenger_chart)

    # RPK
    rpk = base_filtrada[['EMPRESA_SIGLA', 'RPK']].groupby(['EMPRESA_SIGLA']).sum()
    rpk['RPK'] = rpk['RPK'].apply(human_format)
    st.metric(label='RPK', value=rpk.iat[0,0])

    # ASK
    ask = base_filtrada[['EMPRESA_SIGLA', 'ASK']].groupby(['EMPRESA_SIGLA']).sum()
    ask['ASK'] = ask['ASK'].apply(human_format)
    st.metric(label='ASK', value=ask.iat[0,0])

    # Passageiro pagos e grátis
    passageiros = base_filtrada[['EMPRESA_SIGLA', 'PASSAGEIROS_PAGOS', 'PASSAGEIROS_GRATIS']].groupby('EMPRESA_SIGLA', as_index=False).sum()
    passageiros['PASSAGEIROS_PAGOS'] = passageiros['PASSAGEIROS_PAGOS'].apply(human_format)
    passageiros['PASSAGEIROS_GRATIS'] = passageiros['PASSAGEIROS_GRATIS'].apply(human_format)
    st.metric(label='Passageiros Pagos', value=passageiros.iat[0,1])
    st.metric(label='Passageiros Grátis', value=passageiros.iat[0,2])

    # Voos
    grupo_voos = base_filtrada['GRUPO_DE_VOO'].value_counts().to_frame()
    grupo_voos.columns = ['QUANTIDADE']
    grupo_voos.QUANTIDADE = grupo_voos.QUANTIDADE.apply(human_format)
    st.metric(label='Voos Regulares', value=grupo_voos.iat[0,0])
    st.metric(label='Voos Não Regulares', value=grupo_voos.iat[1,0])
    st.metric(label='Voos Improdutivos', value=grupo_voos.iat[2,0])
    print(grupo_voos)

with col[1]:
    # Mapa
    base_map = base_filtrada[['AEROPORTO_DE_DESTINO_UF', 'DECOLAGENS', 'COMBUSTIVEL_LITROS', 'DISTANCIA_VOADA_KM', 'HORAS_VOADAS']].groupby('AEROPORTO_DE_DESTINO_UF', as_index=False).sum()
    base_map.COMBUSTIVEL_LITROS = base_map.COMBUSTIVEL_LITROS.apply(formatar)
    base_map.DISTANCIA_VOADA_KM = base_map.DISTANCIA_VOADA_KM.apply(formatar)
    base_map.HORAS_VOADAS = base_map.HORAS_VOADAS.apply(formatar)
    choropleth = make_choropleth(base_map)
    st.markdown('#### Análise por estado')
    st.plotly_chart(choropleth, use_container_width=True)
    
    base_filtrada['MES'] = base_filtrada['MES'].apply(lambda x: calendar.month_abbr[x])
    decolagens_mes = base_filtrada[['MES', 'AEROPORTO_DE_DESTINO_REGIAO', 'DECOLAGENS']].groupby(['MES', 'AEROPORTO_DE_DESTINO_REGIAO'], as_index=False).sum()
    decolagens = base_filtrada[['MES', 'DECOLAGENS']].groupby(['MES'], as_index=False).sum()
    decolagens_mes['MES'] = pd.Categorical(decolagens_mes['MES'], categories=MONTHS_ORDER, ordered=True)
    decolagens_mes = decolagens_mes.sort_values(by='MES', ignore_index=True)
    decolagens['MES'] = pd.Categorical(decolagens['MES'], categories=MONTHS_ORDER, ordered=True)
    decolagens = decolagens.sort_values(by='MES', ignore_index=True)
    bar_chart = alt.Chart(decolagens_mes).mark_bar().encode(
        y = alt.Y('DECOLAGENS', title='Decolagens'),
        x = alt.X('MES', sort=None, title='Mês'),
        color=alt.Color('AEROPORTO_DE_DESTINO_REGIAO', title='Região').scale(scheme="plasma")
    )
    # Gráfico decolagens por região
    st.markdown('#### Decolagens por região')
    st.altair_chart(bar_chart, use_container_width=True)

    # Gráfico decolagens por mês
    st.markdown('#### Total decolagens por mês')
    st.line_chart(data=decolagens, x='MES', y='DECOLAGENS', width=250, height=250, color=('#ffaa00'))



with col[2]:
    consumo_combustivel = base_filtrada[['MES', 'COMBUSTIVEL_LITROS']].groupby(['MES'], as_index=False).sum() 
    consumo_combustivel['MES'] = pd.Categorical(consumo_combustivel['MES'], categories=MONTHS_ORDER, ordered=True)
    consumo_combustivel = consumo_combustivel.sort_values(by='MES', ignore_index=True)
    st.markdown('#### Consumo combustível')
    st.dataframe(consumo_combustivel,
                 column_order=("MES", "COMBUSTIVEL_LITROS"),
                 hide_index=True,
                 width=None,
                 column_config={
                    "MES": st.column_config.TextColumn(
                        "Mês",
                    ),
                    "COMBUSTIVEL_LITROS": st.column_config.ProgressColumn(
                        "Consumo Combustível",
                        format="%f",
                        min_value=0,
                        max_value=max(consumo_combustivel.COMBUSTIVEL_LITROS),
                     )}
                 )
    with st.expander('Informações', expanded=True):
        st.write('''
            - Dados: [ANAC](https://www.anac.gov.br/acesso-a-informacao/dados-abertos/areas-de-atuacao/voos-e-operacoes-aereas/dados-estatisticos-do-transporte-aereo).
            - :orange[**Revenue Passenger Kilometers (RPK)**]: Quantidade total de receita gerada por uma companhia aérea a partir do transporte de passageiros por quilômetro voado.
            - :orange[**Available Seat Kilometers (ASK)**]: Capacidade da companhia aérea de oferecer assentos disponíveis por quilômetro voado.
            - :orange[**Air Passanger Load Factor (Load Factor)**]: Divisão entre RPK e ASK  
            ''')