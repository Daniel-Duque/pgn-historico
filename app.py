import streamlit as st
import numpy as np
import json 
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import seaborn as sns
from io import BytesIO
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from streamlit_option_menu import option_menu

from utils import DIC_COLORES, convert_df, get_dic_colors, get_dic_colors_area, create_dataframe_sankey

st.set_page_config(layout='wide', page_title="ofiscal - Finanzas Territoriales", page_icon='imgs/favicon.jpeg')

df = pd.read_csv('datasets/gastos_def_2024.csv')
df2 = pd.read_csv('datasets/datos_desagregados_2025.csv')
df2025 = pd.read_csv('datasets/ley_2025.csv')
inc = pd.read_csv('datasets/ingresos_pgn.csv')
inc['Valor_24_esc'] = (inc['Valor_24'] / 1_000_000_000).round(1)
df['Apropiación a precios corrientes'] /= 1000000000
df['Apropiación a precios constantes (2024)'] /= 1000000000
years = list(df['Año'].unique())
years = [int(year) for year in years]
sectors = list(df['Sector'].unique())
entities = list(df['Entidad'].unique())
dict_gasto = {'Funcionamiento':DIC_COLORES['az_verd'][2],
              'Deuda':DIC_COLORES['ax_viol'][1],
              'Inversión':DIC_COLORES['ro_am_na'][3]}

dict_ingreso = {'INGRESOS CORRIENTES DE LA NACIÓN':"white",
       'RECURSOS DE CAPITAL DE LA NACIÓN':"white", 
       'INGRESOS DE LOS ESTABLECIMIENTOS PÚBLICOS':DIC_COLORES['ro_am_na'][3],
       'CONTRIBUCIONES PARAFISCALES DE LA NACIÓN':"white",
       'FONDOS ESPECIALES DE LA NACIÓN':"white"}

dict_pat_ingreso = {'INGRESOS CORRIENTES DE LA NACIÓN':".",
       'RECURSOS DE CAPITAL DE LA NACIÓN':"x", 
       'INGRESOS DE LOS ESTABLECIMIENTOS PÚBLICOS':"",
       'CONTRIBUCIONES PARAFISCALES DE LA NACIÓN':"-",
       'FONDOS ESPECIALES DE LA NACIÓN':"+"}

show = False


prices = {"corrientes": 'Apropiación a precios corrientes',
          "constantes 2024": 'Apropiación a precios constantes (2024)'}

#with st.sidebar:
#    selected_option = option_menu("Menú", ["Main", "Histórico general", "Histórico por sector", "Histórico por entidad", "Treemap", "Descarga de datos"], 
#        icons=['arrow-right-short', 'file-bar-graph', 'intersect', "list-task", 'columns', 'cloud-download'], 
#        menu_icon="p", default_index=0, orientation="vertical")
st.image("imgs/transp.png")
st.divider()

selected_option = option_menu(None, ["Main", 
                                     "Ingresos", 
                                     "Gastos", 
                                     "Treemap", 
                                     "Ejecución",
                                     "Recaudo", 
                                     "Proyecto - 2025",
                                     "Descarga de datos"], 
        icons=['arrow-right-short', 
               'file-bar-graph', 
               'intersect', 
               'columns',
               "list-task",
               "database", 
               'pencil-square',
               'cloud-download'], 
        menu_icon="p", default_index=0, orientation="horizontal")    
    

    
if selected_option == "Main":
    pass

elif selected_option == 'Ingresos':
    tab1, tab2, tab3 = st.tabs(['General', 'Por sector', 'Por entidad'])

    with tab1:
        piv_year = inc.groupby('Año')['Valor_24_esc'].sum().reset_index()
        fig = make_subplots(rows=1, cols=2, x_title='Año',  )
        
        fig.add_trace(
            go.Line(
                x=piv_year['Año'], y=piv_year['Valor_24_esc'], 
                name='Ingreso', line=dict(color=DIC_COLORES['ax_viol'][1])
            ),
            row=1, col=1
        )

        piv_tipo_ingreso = (inc
                        .groupby(['Año', 'Ingreso_alt'])['Valor_24_esc']
                        .sum()
                        .reset_index())
        piv_tipo_ingreso['total'] = piv_tipo_ingreso.groupby(['Año'])['Valor_24_esc'].transform('sum')

        piv_tipo_ingreso['%'] = ((piv_tipo_ingreso['Valor_24_esc'] / piv_tipo_ingreso['total']) * 100).round(2)

        val = 0.2
        for i, group in piv_tipo_ingreso.groupby('Ingreso_alt'):
            fig.add_trace(go.Bar(
                x=group['Año'],
                y=group['%'],
                name=i, marker_color=dict_ingreso[i], 
                marker_pattern_shape=dict_pat_ingreso[i],
                marker_pattern_bgcolor=DIC_COLORES['az_verd'][2],
                marker_pattern_size=6,
                opacity=val
            ),  row=1, col=2)
            val += 0.2

        fig.update_layout(barmode='stack', hovermode='x unified')
        fig.update_layout(width=1000, height=500, legend=dict(orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1), title='Histórico general <br><sup>Cifras en miles de millones de pesos</sup>', yaxis_tickformat='.0f')


        st.plotly_chart(fig)  

        piv_year = inc.groupby(['Año', 'Ingreso_alt'])['Valor_24_esc'].sum().reset_index()
        fig = make_subplots(rows=1, cols=1, x_title='Año',  )

        for n, i in enumerate(piv_year['Ingreso_alt'].unique()):
            filtro = piv_year[piv_year['Ingreso_alt'] == i]       
            fig.add_trace(
                go.Line(
                    x=filtro['Año'], y=filtro['Valor_24_esc'], 
                    name=i, line=dict(color=DIC_COLORES['ro_am_na'][n]),
                ),
                row=1, col=1
            )
            print(n)  
        fig.update_layout(barmode='stack', hovermode='x unified')
        fig.update_layout(width=1000, height=500, legend=dict(orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1), title='Histórico general <br><sup>Cifras en miles de millones de pesos</sup>', yaxis_tickformat='.0f')
        st.plotly_chart(fig)

    with tab2:
        d = inc[inc['Sector'] != 'Nación']
        sectors = d['Sector'].unique().tolist()
        sector = st.selectbox("Seleccione un sector: ", sectors, key=20)
        fil_sector = d[d['Sector'] == sector]
        piv_sec = fil_sector.groupby('Año')['Valor_24_esc'].sum().reset_index()

        fig = make_subplots(rows=1, cols=2, x_title='Año',  )
            
        fig.add_trace(
                go.Line(
                    x=piv_sec['Año'], y=piv_sec['Valor_24_esc'], 
                    name='Valor', line=dict(color=DIC_COLORES['ax_viol'][1])
                ),
                row=1, col=1
            )

        piv_sector = (fil_sector
                            .groupby(['Año', 'Ingreso específico'])['Valor_24_esc']
                            .sum()
                            .reset_index())

        piv_sector['total'] = piv_sector.groupby(['Año'])['Valor_24_esc'].transform('sum')

        piv_sector['%'] = ((piv_sector['Valor_24_esc'] / piv_sector['total']) * 100).round(2)

                
        for i, group in piv_sector.groupby('Ingreso específico'):
                fig.add_trace(go.Bar(
                    x=group['Año'],
                    y=group['%'],
                    name=i
                ), row=1, col=2)

        fig.update_layout(barmode='stack', hovermode='x unified')
        fig.update_layout(width=1000, height=500, legend=dict(orientation="h",
            yanchor="bottom",
            y=-0.24,
            xanchor="right",
            x=1), title='Histórico por sector<br><sup>Cifras en miles de millones de pesos</sup>', yaxis_tickformat='.0f')


        st.plotly_chart(fig, key=1)

    with tab3:
        d = inc[inc['Sector'] != 'Nación']
        sector = st.selectbox("Seleccione un sector: ", sectors)
        d = d[d['Sector'] == sector]
        ents = d['Entidad'].unique().tolist()
        ent = st.selectbox("Seleccione una entidad: ", ents, key=4)
        fil_ent = d[d['Entidad'] == ent]
        piv_ent = fil_ent.groupby('Año')['Valor_24_esc'].sum().reset_index()

        fig = make_subplots(rows=1, cols=2, x_title='Año',  )
            
        fig.add_trace(
                go.Line(
                    x=piv_ent['Año'], y=piv_ent['Valor_24_esc'], 
                    name='Valor', line=dict(color=DIC_COLORES['ax_viol'][1])
                ),
                row=1, col=1
            )

        piv_entidad = (fil_ent
                            .groupby(['Año', 'Ingreso específico'])['Valor_24_esc']
                            .sum()
                            .reset_index())
        piv_entidad['total'] = piv_entidad.groupby(['Año'])['Valor_24_esc'].transform('sum')

        piv_entidad['%'] = ((piv_entidad['Valor_24_esc'] / piv_entidad['total']) * 100).round(2)

                
        for i, group in piv_entidad.groupby('Ingreso específico'):
                fig.add_trace(go.Bar(
                    x=group['Año'],
                    y=group['%'],
                    name=i
                ), row=1, col=2)

        fig.update_layout(barmode='stack', hovermode='x unified')
        fig.update_layout(width=1000, height=500, legend=dict(orientation="h",
            yanchor="bottom",
            y=-0.24,
            xanchor="right",
            x=1), title='Histórico por entidad <br><sup>Cifras en miles de millones de pesos</sup>', yaxis_tickformat='.0f')


        st.plotly_chart(fig, key=12)



elif selected_option == "Gastos":

    tab1, tab2, tab3 = st.tabs(['General',
                                'Por sector',
                                'Por entidad'])
    with tab1:

        piv_2024 = df.groupby('Año')['Apropiación a precios constantes (2024)'].sum().reset_index()
        tasa_gen_cagr = (piv_2024[piv_2024['Año'] == 2024]['Apropiación a precios constantes (2024)'].reset_index(drop=True)/ piv_2024[piv_2024['Año'] == 2013]['Apropiación a precios constantes (2024)'].reset_index(drop=True))[0] ** (1/(2024 - 2013)) - 1        
        piv_2024['CAGR'] = tasa_gen_cagr
        piv_corr = df.groupby('Año')['apropiacion_corrientes'].sum().reset_index()

        #piv_2024['Apropiación a precios constantes (2024)'] /= 1000

        fig = make_subplots(rows=1, cols=2, x_title='Año',  )
        
        fig.add_trace(
            go.Line(
                x=piv_2024['Año'], y=piv_2024['Apropiación a precios constantes (2024)'], 
                name='Apropiación a precios constantes (2024)', line=dict(color=DIC_COLORES['ax_viol'][1])
            ),
            row=1, col=1
        )

        piv_tipo_gasto = (df
                        .groupby(['Año', 'Tipo de gasto'])['Apropiación a precios constantes (2024)']
                        .sum()
                        .reset_index())
        piv_tipo_gasto['total'] = piv_tipo_gasto.groupby(['Año'])['Apropiación a precios constantes (2024)'].transform('sum')

        piv_tipo_gasto['%'] = ((piv_tipo_gasto['Apropiación a precios constantes (2024)'] / piv_tipo_gasto['total']) * 100).round(2)



            
        for i, group in piv_tipo_gasto.groupby('Tipo de gasto'):
            fig.add_trace(go.Bar(
                x=group['Año'],
                y=group['%'],
                name=i, marker_color=dict_gasto[i]
            ), row=1, col=2)

        fig.update_layout(barmode='stack', hovermode='x unified')
        fig.update_layout(width=1000, height=500, legend=dict(orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1), title='Histórico general <br><sup>Cifras en miles de millones de pesos</sup>', yaxis_tickformat='.0f')


        st.plotly_chart(fig, key=1)

    with tab2:

    

        sector = st.selectbox("Seleccione el sector", sectors, key=2)
        filter_sector = df[df['Sector'] == sector]

        pivot_sector = filter_sector.pivot_table(index='Año', values=prices.values(), aggfunc='sum').reset_index()

        fig = make_subplots(rows=1, cols=2, x_title='Año', shared_yaxes=True)
        
        fig.add_trace(
            go.Line(
                x=pivot_sector['Año'], y=pivot_sector['Apropiación a precios constantes (2024)'], 
                name='Apropiación a precios constantes (2024)', line=dict(color=DIC_COLORES['ax_viol'][1])
            ),
            row=1, col=1
        )

        piv_tipo_gasto_sector = (filter_sector
                        .groupby(['Año', 'Tipo de gasto'])['Apropiación a precios constantes (2024)']
                        .sum()
                        .reset_index())
        for i, group in piv_tipo_gasto_sector.groupby('Tipo de gasto'):
            fig.add_trace(go.Bar(
                x=group['Año'],
                y=group['Apropiación a precios constantes (2024)'],
                name=i, marker_color=dict_gasto[i]
            ), row=1, col=2)

        fig.update_layout(barmode='stack', hovermode='x unified')


        fig.update_layout(width=1000, height=500, legend=dict(orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1), title=f"{sector} <br><sup>Cifras en miles de millones de pesos</sup>", yaxis_tickformat='.0f')

        st.plotly_chart(fig, key=20)

        st.subheader(f"Variación histórica por sector: {sector}")



        pivot_sector = pivot_sector.set_index('Año')
        pivot_sector['pct'] = pivot_sector['Apropiación a precios constantes (2024)'].pct_change()
        pivot_sector['pct'] = (pivot_sector['pct'] * 100).round(2)
        den = max(pivot_sector.index) - min(pivot_sector.index)
        pivot_sector['CAGR'] = ((pivot_sector.loc[max(pivot_sector.index), 'Apropiación a precios constantes (2024)'] / pivot_sector.loc[min(pivot_sector.index), 'Apropiación a precios constantes (2024)']) ** (1/11)) - 1
        pivot_sector['CAGR'] = (pivot_sector['CAGR'] * 100).round(2)
        pivot_sector['CAGR_gen'] = (tasa_gen_cagr * 100).round(2)
        pivot_sector = pivot_sector.reset_index()

        fig = make_subplots(rows=1, cols=2, x_title='Año')

        fig.add_trace(
                go.Bar(x=pivot_sector['Año'], y=pivot_sector['Apropiación a precios constantes (2024)'],
                    name='Apropiación a precios constantes (2024)', marker_color=DIC_COLORES['ofiscal'][1]),
                row=1, col=1, 
            )

        fig.add_trace(go.Line(
                    x=pivot_sector['Año'], 
                    y=pivot_sector['pct'], 
                    name='Variación porcentual (%)', line=dict(color=DIC_COLORES['ro_am_na'][1])
                ),
                row=1, col=2
            )
        fig.add_trace(
                go.Line(
                    x=pivot_sector['Año'], y=pivot_sector['CAGR'], name='Variación anualizada sector (%)', line=dict(color=DIC_COLORES['verde'][0])
                ),
                row=1, col=2
            )
        fig.add_trace(
                go.Line(
                    x=pivot_sector['Año'], y=pivot_sector['CAGR_gen'], name='Variación anualizada PGN (%)', line=dict(color=DIC_COLORES['ax_viol'][2])
                ),
                row=1, col=2
            )
        fig.update_layout(width=1000, height=500, legend=dict(orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1), hovermode='x unified', yaxis_tickformat='.0f', title=f"{sector} <br><sup>Cifras en miles de millones de pesos</sup>")

        st.plotly_chart(fig, key=30)

    with tab3:
    
        sector = st.selectbox("Seleccione el sector", sectors, key=3)
        filter_sector = df[df['Sector'] == sector]
    
        entities_sector = filter_sector['Entidad'].unique()
        entidad = st.selectbox("Seleccione la entidad",
                                entities_sector)
        
        filter_entity = filter_sector[filter_sector['Entidad'] == entidad]

        pivot_entity = filter_entity.pivot_table(index='Año',
                                            values=prices.values(),
                                            aggfunc='sum')
        
        pivot_entity = pivot_entity.reset_index()

        fig = make_subplots(rows=1, cols=2, x_title='Año', shared_yaxes=True)
        
        fig.add_trace(
            go.Line(
                x=pivot_entity['Año'], y=pivot_entity['Apropiación a precios constantes (2024)'], 
                name='Apropiación a precios constantes (2024)', line=dict(color=DIC_COLORES['ax_viol'][1])
            ),
            row=1, col=1
        )
        piv_tipo_gasto_entity = (filter_entity
                        .groupby(['Año', 'Tipo de gasto'])['Apropiación a precios constantes (2024)']
                        .sum()
                        .reset_index())
        for i, group in piv_tipo_gasto_entity.groupby('Tipo de gasto'):
            fig.add_trace(go.Bar(
                x=group['Año'],
                y=group['Apropiación a precios constantes (2024)'],
                name=i, marker_color=dict_gasto[i]
            ), row=1, col=2)

        fig.update_layout(barmode='stack', hovermode='x unified')

        fig.update_layout(width=1000, height=500, legend=dict(orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1), title=f"{entidad} <br><sup>Cifras en miles de millones de pesos</sup>", yaxis_tickformat='.0f')

        st.plotly_chart(fig, key=40)

        if pivot_entity['Año'].nunique() <=1:
            st.warning(f"La entidad {entidad} solo tiene información de un año.")
            st.stop()

        st.subheader(f"Variación histórica por entidad: {entidad}")

        pivot_entity = pivot_entity.set_index('Año')
        pivot_entity['pct'] = pivot_entity['Apropiación a precios constantes (2024)'].pct_change()
        pivot_entity['pct'] = (pivot_entity['pct'] * 100).round(2)
        den = max(pivot_entity.index) - min(pivot_entity.index)
        pivot_entity['CAGR'] = ((pivot_entity.loc[max(pivot_entity.index), 'Apropiación a precios constantes (2024)'] / pivot_entity.loc[min(pivot_entity.index), 'Apropiación a precios constantes (2024)'] ) ** (1/den)) - 1
        pivot_entity['CAGR'] = (pivot_entity['CAGR'] * 100).round(2)
        pivot_entity['CAGR_gen'] = (tasa_gen_cagr * 100).round(2)
        pivot_entity = pivot_entity.reset_index()

        fig = make_subplots(rows=1, cols=2, x_title='Año')

        fig.add_trace(
            go.Bar(x=pivot_entity['Año'], y=pivot_entity['Apropiación a precios constantes (2024)'],
                name='Apropiación a precios constantes (2024)', marker_color=DIC_COLORES['ofiscal'][1]),
            row=1, col=1, 
        )

        fig.add_trace(go.Line(
                x=pivot_entity['Año'], 
                y=pivot_entity['pct'], 
                name='Variación porcentual (%)', line=dict(color=DIC_COLORES['ro_am_na'][1])
            ),
            row=1, col=2
        )
        fig.add_trace(
            go.Line(
                x=pivot_entity['Año'], y=pivot_entity['CAGR'], name='Variación anualizada (%)', line=dict(color=DIC_COLORES['verde'][0])
            ),
            row=1, col=2
        )
        fig.add_trace(
                go.Line(
                    x=pivot_entity['Año'], y=pivot_entity['CAGR_gen'], name='Variación anualizada PGN (%)', line=dict(color=DIC_COLORES['ax_viol'][2])
                ),
                row=1, col=2
            )
        fig.update_layout(width=1000, height=500, legend=dict(orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1), hovermode='x unified', yaxis_tickformat='.0f', title=f"{entidad} <br><sup>Cifras en miles de millones de pesos</sup>")

        st.plotly_chart(fig, key=50)

elif selected_option == "Treemap":

    tab1, tab2 = st.tabs(['Ingreso', 'Gasto'])
    with tab1:

        year = st.slider("Seleccione el año (ingreso)", 
                        min_value=min(years),
                        max_value=max(years))
        filter_inc = inc[inc['Año'] == year]

        fig = px.treemap(filter_inc, 
                        path=[px.Constant('PGN'),     'Ingreso', 
                                'Ingreso específico'],
                        values='Valor_24_esc',
                        color_discrete_sequence=[DIC_COLORES['ax_viol'][1],
                                                 DIC_COLORES['ro_am_na'][3],
                                                 DIC_COLORES['az_verd'][2]],
                        title="Matriz de composición anual de ingreso del PGN <br><sup>Cifras en miles de millones de pesos</sup>")
        
        fig.update_layout(width=1000, height=600)
        
        st.plotly_chart(fig)

    with tab2:
        year = st.slider("Seleccione el año", 
                        min_value=min(years),
                        max_value=max(years))

        filter_year = df[df['Año'] == year]
    

        dic_treemap = get_dic_colors(filter_year)
        dic_treemap['(?)'] = "#D9D9ED"
        fig = px.treemap(filter_year, 
                        path=[px.Constant('PGN'),     'Sector', 
                                'Entidad', 
                                'Tipo de gasto'],
                        values='Apropiación a precios constantes (2024)',
                        color='Sector',
                        color_discrete_map=dic_treemap,
                        title="Matriz de composición anual de gasto del PGN <br><sup>Cifras en miles de millones de pesos</sup>")
        
        fig.update_layout(width=1000, height=600)
    
        st.plotly_chart(fig)

elif selected_option == 'Ejecución':
    months = [
        "Ene", "Feb", "Mar", "Abr", "May", "Jun",
        "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"
    ]



    df_ejec = pd.read_csv('datasets/ejecucion_agosto.csv')

    total_ap = (df_ejec.groupby('mes_num')['APR. VIGENTE'].sum() / 1_000_000_000_000).round(1)
    total_ej = (df_ejec.groupby('mes_num')['OBLIGACION'].sum() / 1_000_000_000_000).round(1)
    total_co = (df_ejec.groupby('mes_num')['COMPROMISO'].sum() / 1_000_000_000_000).round(1)
    total_ej_perc = (df_ejec.groupby('mes_num')['perc_ejecucion'].sum() * 100).round(1)
    total_co_perc = (df_ejec.groupby('mes_num')['perc_compr'].sum() * 100).round(1)

    

    sectores = df_ejec['Sector'].unique().tolist()
    entidades = df_ejec['Entidad'].unique().tolist()

    tab1, tab2, tab3 = st.tabs(["Vista general",
                                "Navegación detallada",
                                "Descarga de datos"])

    with tab1:
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Apr. Vigente (bil)", total_ap[8])
        with col2: 
            st.metric("Ejecutado (bil)", total_ej[8])
        with col3:
            st.metric("Comprometido (bil)", total_co[8])
        with col4:
            st.metric("% ejecutado (al mes actual)", total_ej_perc[8])
        with col5:
            st.metric("% comprometido (al mes actual)", total_co_perc[8])

        fig = make_subplots(rows=1, cols=2, subplot_titles=("Valores (billones)", "Porcentaje (%)"))

        mean_growth_rate = (total_ej.loc[8] / 8)
        forecast_values = [mean_growth_rate * i  for i in range(9, 13)]
        full_values_ej = list(total_ej.values) + forecast_values
        full_values_ej = [round(i, 1) for i in full_values_ej]
        fig.add_trace(go.Scatter(x=months[:9], 
                                y=full_values_ej[:9], 
                                mode='lines+markers',
                                name='Ejecutado', showlegend=False,
                                line=dict(color='#dd722a')), row=1, col=1)

        # Highlight the forecasted part with a red dashed line (the last 4 points)
        fig.add_trace(go.Scatter(
            x=months[8:],  # x-axis for forecasted values
            y=full_values_ej[8:],     # The forecasted values
            mode='lines+markers',          # Just lines (no markers here)
            name='Pronóstico', 
            line=dict(color='#81D3CD', width=2, dash='dash'),
            marker=dict(color='#81D3CD', size=8),  # Dashed line for forecast
        ), row=1, col=1)

        mean_growth_rate = (total_co.loc[8] / 8)
        forecast_values = [mean_growth_rate * i  for i in range(9, 13)]
        full_values_co = list(total_co.values) + forecast_values
        full_values_co = [round(i, 1) for i in full_values_co]


        fig.add_trace(go.Scatter(x=months[:9], 
                                y=full_values_co[:9], 
                                mode='lines+markers', 
                                name='Comprometido', showlegend=False,
                                line=dict(color='#2635bf')), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=months[8:],  # x-axis for forecasted values
            y=full_values_co[8:],     # The forecasted values
            mode='lines+markers',          # Just lines (no markers here)
            name='Pronóstico', showlegend=False,
            line=dict(color='#81D3CD', width=2, dash='dash'),
            marker=dict(color='#81D3CD', size=8),  # Dashed line for forecast
        ), row=1, col=1)

        fig.add_shape(type='line', x0=0, x1=11, y0=total_ap[8], y1=total_ap[8], line=dict(color='#2635bf', dash='dash'),
                    row=1, col=1)

        
        mean_growth_rate = (total_ej_perc.loc[8] / 8)
        forecast_values = [mean_growth_rate * i  for i in range(9, 13)]
        full_values_perc = list(total_ej_perc.values) + forecast_values
        full_values_perc = [round(i, 1) for i in full_values_perc]

        fig.add_trace(go.Scatter(x=months[:9], 
                                y=full_values_perc[:9], 
                                mode='lines+markers', 
                                name='Ejecutado', 
                                line=dict(color='#dd722a')), row=1, col=2)

        fig.add_trace(go.Scatter(
            x=months[8:],  # x-axis for forecasted values
            y=full_values_perc[8:],     # The forecasted values
            mode='lines+markers',          # Just lines (no markers here)
            name='Pronóstico', showlegend=False,
            line=dict(color='#81D3CD', width=2, dash='dash'),
            marker=dict(color='#81D3CD', size=8),  # Dashed line for forecast
        ), row=1, col=2)



        mean_growth_rate = (total_co_perc.loc[8] / 8)
        forecast_values = [mean_growth_rate * i  for i in range(9, 13)]
        full_values_co = list(total_co_perc.values) + forecast_values
        full_values_co = [round(i, 1) for i in full_values_co]

        fig.add_trace(go.Scatter(x=months[:9], 
                                y=full_values_co[:9], 
                                mode='lines+markers', 
                                name='Comprometido', 
                                line=dict(color='#2635bf')),  row=1, col=2)
        fig.add_trace(go.Scatter(
            x=months[8:],  # x-axis for forecasted values
            y=full_values_co[8:],     # The forecasted values
            mode='lines+markers',          # Just lines (no markers here)
            name='Pronóstico', showlegend=False,
            line=dict(color='#81D3CD', width=2, dash='dash'),
            marker=dict(color='#81D3CD', size=8),  # Dashed line for forecast
        ), row=1, col=2)

        fig.add_shape(type='line', x0=0, x1=11, y0=100, y1=100, line=dict(color='#2635bf', dash='dash'),
                    row=1, col=2)

        fig.update_layout(
            title="Ejecución y compromiso general al mes de agosto",
            height=400, 
            width=900,
            legend=dict(
                orientation='h',   # Horizontal legend
                x=0.64,             # Center the legend
                y=1.1,             # Position it slightly above the plots
                xanchor='left',  # Center the legend horizontally
                yanchor='bottom'   # Align the legend vertically
            )
        )
        st.plotly_chart(fig)

        perd_aprop = 100 - full_values_co[-1]

        if perd_aprop > 0:
            st.error(f"Hay una pérdida de apropiación del {round(perd_aprop, 2)}%.")
        else:
            st.success(f"No hay pérdida de apropiación.")

        piv_s = (df_ejec[df_ejec['mes_num'] == 8].pivot_table(index='Sector',
                                    values=['APR. VIGENTE','OBLIGACION', 'COMPROMISO'],
                                    aggfunc='sum')
                                    .assign(perc_ejecucion=lambda x: (x['OBLIGACION'] / x['APR. VIGENTE'] * 100).round(1),
                                            perc_compr=lambda x: (x['COMPROMISO'] / x['APR. VIGENTE'] * 100).round(1)))
        bots_ejec = piv_s.sort_values(by='perc_ejecucion', ascending=True).head(10).reset_index()
        bots_compr = piv_s.sort_values(by='perc_compr', ascending=True).head(10).reset_index()
        tops_ejec = piv_s.sort_values(by='perc_ejecucion', ascending=True).tail(10).reset_index()
        tops_compr = piv_s.sort_values(by='perc_compr', ascending=True).tail(10).reset_index()


        fig = make_subplots(rows=1, cols=2, subplot_titles=("Ejecutado (%)", "Comprometido (%)"))

    # Plot absolute values as bar plots in the first subplot
        fig.add_trace(go.Bar(y=tops_ejec['Sector'], 
                            x=tops_ejec['perc_ejecucion'], 
                            name='Ejecutado', 
                            marker_color='#F7B261', 
                            orientation='h',
                            text=tops_ejec['Sector'],
                            textposition='inside',
                            hoverinfo='x'), row=1, col=1)
        fig.add_trace(go.Bar(y=tops_compr['Sector'], 
                            x=tops_compr['perc_compr'], 
                            name='Comprometido', 
                            marker_color='#81D3CD', 
                            orientation='h',
                            text=tops_compr['Sector'],
                            textposition='inside',
                            hoverinfo='x'), row=1, col=2)
        fig.add_shape(
            type='line',
            x0=100, x1=100, y0=-0.5, y1=9.5,  # Set x0, x1 for the vertical line position
            line=dict(color='#dd722a', width=1, dash='dash'),
            row=1, col=1
        )
        fig.add_shape(
            type='line',
            x0=100, x1=100, y0=-0.5, y1=9.5,  # Set x0, x1 for the vertical line position
            line=dict(color='#81D3CD', width=1, dash='dash'),
            row=1, col=2
        )
        fig.update_yaxes(showticklabels=False)
        fig.update_layout(
            title="Top 10 sectores con mayor ejecución (al mes de agosto) ",
            height=400, 
            width=900,
            legend=dict(
                orientation='h',   # Horizontal legend
                x=0.72,             # Center the legend
                y=1.1,             # Position it slightly above the plots
                xanchor='left',  # Center the legend horizontally
                yanchor='bottom'   # Align the legend vertically
            )
        )
        st.plotly_chart(fig)

        # peor ejecución
        fig = make_subplots(rows=1, cols=2, subplot_titles=("Ejecutado (%)", "Comprometido (%)"))

        fig.add_trace(go.Bar(y=bots_ejec['Sector'], 
                            x=bots_ejec['perc_ejecucion'], 
                            name='Ejecutado', 
                            marker_color='#F7B261', 
                            orientation='h',
                            text=bots_ejec['Sector'],
                            textposition='inside',
                            hoverinfo='x'), row=1, col=1)
        fig.add_trace(go.Bar(y=bots_compr['Sector'], 
                            x=bots_compr['perc_compr'], 
                            name='Comprometido', 
                            marker_color='#81D3CD', 
                            orientation='h',
                            text=bots_compr['Sector'],
                            textposition='inside',
                            hoverinfo='x'), row=1, col=2)
        fig.add_shape(
            type='line',
            x0=100, x1=100, y0=-0.5, y1=9.5,  # Set x0, x1 for the vertical line position
            line=dict(color='#dd722a', width=1, dash='dash'),
            row=1, col=1
        )
        fig.add_shape(
            type='line',
            x0=100, x1=100, y0=-0.5, y1=9.5,  # Set x0, x1 for the vertical line position
            line=dict(color='#81D3CD', width=1, dash='dash'),
            row=1, col=2
        )
        fig.update_yaxes(showticklabels=False)
        fig.update_layout(
            title="Top 10 sectores con menor ejecución (al mes de agosto) ",
            height=400, 
            width=900,
            legend=dict(
                orientation='h',   # Horizontal legend
                x=0.72,             # Center the legend
                y=1.1,             # Position it slightly above the plots
                xanchor='left',  # Center the legend horizontally
                yanchor='bottom'   # Align the legend vertically
            )
        )
        st.plotly_chart(fig)

        piv_e = (df_ejec[df_ejec['mes_num'] == 8].pivot_table(index='Entidad',
                                    values=['APR. VIGENTE','OBLIGACION', 'COMPROMISO'],
                                    aggfunc='sum')
                                    .assign(perc_ejecucion=lambda x: (x['OBLIGACION'] / x['APR. VIGENTE'] * 100).round(1),
                                            perc_compr=lambda x: (x['COMPROMISO'] / x['APR. VIGENTE'] * 100).round(1))
                                    .assign(perc_perdida=lambda x:100 - x['perc_compr']))
        tops_ejec = piv_e.sort_values(by='perc_ejecucion', ascending=True).tail(10).reset_index()
        tops_compr = piv_e.sort_values(by='perc_compr', ascending=True).tail(10).reset_index()
        bots_ejec = piv_e.sort_values(by='perc_ejecucion', ascending=True).head(10).reset_index()
        bots_compr = piv_e.sort_values(by='perc_compr', ascending=True).head(10).reset_index()
        



        fig = make_subplots(rows=1, cols=2, subplot_titles=("Ejecutado (%)", "Pérdida de aprop. (%)"))

    # Plot absolute values as bar plots in the first subplot
        fig.add_trace(go.Bar(y=tops_ejec['Entidad'], 
                            x=tops_ejec['perc_ejecucion'], 
                            name='Ejecutado', 
                            marker_color='#F7B261', 
                            orientation='h',
                            text=tops_ejec['Entidad'],
                            textposition='inside',
                            hoverinfo='x'), row=1, col=1)
        fig.add_trace(go.Bar(y=tops_compr['Entidad'], 
                            x=tops_compr['perc_compr'], 
                            name='Comprometido', 
                            marker_color='#81D3CD', 
                            orientation='h',
                            text=tops_compr['Entidad'],
                            textposition='inside',
                            hoverinfo='x'), row=1, col=2)
        fig.add_shape(
            type='line',
            x0=100, x1=100, y0=-0.5, y1=9.5,  # Set x0, x1 for the vertical line position
            line=dict(color='#dd722a', width=1, dash='dash'),
            row=1, col=1
        )
        fig.add_shape(
            type='line',
            x0=100, x1=100, y0=-0.5, y1=9.5,  # Set x0, x1 for the vertical line position
            line=dict(color='#81D3CD', width=1, dash='dash'),
            row=1, col=2
        )
        fig.update_yaxes(showticklabels=False)
        fig.update_layout(
            title="Top 10 entidades con mayor ejecución (al mes de agosto)",
            height=400, 
            width=900,
            legend=dict(
                orientation='h',   # Horizontal legend
                x=0.72,             # Center the legend
                y=1.1,             # Position it slightly above the plots
                xanchor='left',  # Center the legend horizontally
                yanchor='bottom'   # Align the legend vertically
            )
        )
        st.plotly_chart(fig)

        fig = make_subplots(rows=1, cols=2, subplot_titles=("Ejecutado (%)", "Comprometido (%)"))

    # Plot absolute values as bar plots in the first subplot
        fig.add_trace(go.Bar(y=bots_ejec['Entidad'], 
                            x=bots_ejec['perc_ejecucion'], 
                            name='Ejecutado', 
                            marker_color='#F7B261', 
                            orientation='h',
                            hovertext=bots_ejec['Entidad'],
                            hoverinfo='x+text'), row=1, col=1)
        fig.add_trace(go.Bar(y=bots_compr['Entidad'], 
                            x=bots_compr['perc_compr'], 
                            name='Comprometido', 
                            marker_color='#81D3CD', 
                            orientation='h',
                            hovertext=bots_compr['Entidad'],
                            hoverinfo='x+text'), row=1, col=2)
        fig.add_shape(
            type='line',
            x0=100, x1=100, y0=-0.5, y1=9.5,  # Set x0, x1 for the vertical line position
            line=dict(color='#dd722a', width=1, dash='dash'),
            row=1, col=1
        )
        fig.add_shape(
            type='line',
            x0=100, x1=100, y0=-0.5, y1=9.5,  # Set x0, x1 for the vertical line position
            line=dict(color='#81D3CD', width=1, dash='dash'),
            row=1, col=2
        )
        fig.update_yaxes(showticklabels=False)
        fig.update_layout(
            title="Top 10 entidades con menor ejecución (al mes de agosto)",
            height=400, 
            width=900,
            legend=dict(
                orientation='h',   # Horizontal legend
                x=0.7,             # Center the legend
                y=1.1,             # Position it slightly above the plots
                xanchor='left',  # Center the legend horizontally
                yanchor='bottom'   # Align the legend vertically
            )
        )
        st.plotly_chart(fig)
    
    with tab2:
        st.subheader("Por sector")
        sector = st.selectbox("Seleccione un sector: ", sectores)

        fil_sector = df_ejec[df_ejec['Sector'] == sector]
        piv_sector = (fil_sector.pivot_table(index='mes_num',
                    aggfunc='sum',
                    values=['OBLIGACION', 'APR. VIGENTE', 'COMPROMISO'])
                                .div(1_000_000_000, axis=0)
                                .assign(perc_ejecucion=lambda x: (x['OBLIGACION'] / x['APR. VIGENTE'] * 100),
                                        perc_compr=lambda x: x['COMPROMISO'] / x['APR. VIGENTE'] * 100)
                                .round(1))
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Apr. Vigente (mmil)", piv_sector.loc[8, "APR. VIGENTE"])
        with col2: 
            st.metric("Ejecutado (mmil)", piv_sector.loc[8, "OBLIGACION"])
        with col3:
            st.metric("Comprometido (mmil)", piv_sector.loc[8, "COMPROMISO"])
        with col4:
            st.metric("% ejecutado", piv_sector.loc[8, "perc_ejecucion"])
        with col5:
            st.metric("% comprometido", piv_sector.loc[8, "perc_compr"])


        mean_growth_rate = (piv_sector.loc[8, "perc_ejecucion"] / 8) / 100

        # Step 2: Forecast the next 4 values
        last_value = piv_sector['perc_ejecucion'].iloc[-1]
        forecast_values = [mean_growth_rate * i * 100 for i in range(9, 13)]

        # Combine original and forecasted values
        full_values = piv_sector['perc_ejecucion'].tolist() + forecast_values
        full_values = [round(i, 1) for i in full_values]

        # Step 3: Create a line plot
        fig = make_subplots(rows=1, cols=2, subplot_titles=("Ejecutado (%)", "Comprometido (%)"))

        # Plot the first 8 values (blue solid line)
        fig.add_trace(go.Scatter(
            x=months[:9],  # x-axis for all values (1 to 12)
            y=full_values[:9],         # All values (original + forecast)
            mode='lines+markers',  # Line and markers
            name='Observado', showlegend=False,
            line=dict(color='#2635bf', width=2),  # Solid blue line for all values
            marker=dict(color=['#2635bf']*9, size=8)  # Red markers for forecasted values
        ), row=1, col=1)

        # Highlight the forecasted part with a red dashed line (the last 4 points)
        fig.add_trace(go.Scatter(
            x=months[8:],  # x-axis for forecasted values
            y=full_values[8:],     # The forecasted values
            mode='lines+markers',          # Just lines (no markers here)
            name='Pronóstico', showlegend=False,
            line=dict(color='#dd722a', width=2, dash='dash'),
            marker=dict(color='#dd722a', size=8),  # Dashed line for forecast
        ), row=1, col=1)

        mean_growth_rate = (piv_sector.loc[8, "perc_compr"] / 8) / 100

        # Step 2: Forecast the next 4 values
        last_value = piv_sector['perc_compr'].iloc[-1]
        forecast_values = [mean_growth_rate * i * 100 for i in range(9, 13)]

        # Combine original and forecasted values
        full_values = piv_sector['perc_compr'].tolist() + forecast_values
        full_values = [round(i, 1) for i in full_values]

        fig.add_trace(go.Scatter(
            x=months[:9],  # x-axis for all values (1 to 12)
            y=full_values[:9],         # All values (original + forecast)
            mode='lines+markers',  # Line and markers
            name='Observado',
            line=dict(color='#2635bf', width=2), # Solid blue line for all values
            marker=dict(color=['#2635bf']*9, size=8)  # Red markers for forecasted values
        ), row=1, col=2)



        # Highlight the forecasted part with a red dashed line (the last 4 points)
        fig.add_trace(go.Scatter(
            x=months[8:],  # x-axis for forecasted values
            y=full_values[8:],     # The forecasted values
            mode='lines+markers',          # Just lines (no markers here)
            name='Pronóstico',
            line=dict(color='#dd722a', width=2, dash='dash'),
            marker=dict(color='#dd722a', size=8),  # Dashed line for forecast
        ), row=1, col=2)

        fig.add_shape(type='line', x0=0, x1=11, y0=100, y1=100, line=dict(color='#2635bf', dash='dash'),
                    row=1, col=2)
        fig.add_shape(type='line', x0=0, x1=11, y0=100, y1=100, line=dict(color='#2635bf', dash='dash'),
                    row=1, col=1)
        fig.update_yaxes(range=[0, max(100, max(full_values))]) 

        fig.update_layout(
            title=f"Ejecución y compromiso al mes de agosto por sector: {sector}",
            height=400, 
            width=900,
            legend=dict(
                orientation='h',
                yanchor="bottom",
                y=1.1,
                xanchor="right",
                x=1   # Align the legend vertically
            )
        )

        # Show the plot
        st.plotly_chart(fig)

        perd_aprop = 100 - full_values[-1]

        if perd_aprop > 0:
            st.error(f"Hay una pérdida de apropiación del {round(perd_aprop, 2)}% para el sector {sector}.")
        else:
            st.success(f"No hay pérdida de apropiación para el sector {sector}.")

        st.subheader("Por entidad")
        entidad = st.selectbox("Seleccione una entidad: ", entidades)
        fil_entidad = df_ejec[df_ejec['Entidad'] == entidad]
        piv_entidad = (fil_entidad.pivot_table(index='mes_num',
                    aggfunc='sum',
                    values=['OBLIGACION', 'APR. VIGENTE', 'COMPROMISO'])
                                .div(1_000_000_000, axis=0)
                                .assign(perc_ejecucion=lambda x: (x['OBLIGACION'] / x['APR. VIGENTE'] * 100),
                                        perc_compr=lambda x: x['COMPROMISO'] / x['APR. VIGENTE'] * 100)
                                .round(1))
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Apr. Vigente (mmil)", piv_entidad.loc[8, "APR. VIGENTE"])
        with col2: 
            st.metric("Ejecutado (mmil)", piv_entidad.loc[8, "OBLIGACION"])
        with col3:
            st.metric("Comprometido (mmil)", piv_entidad.loc[8, "COMPROMISO"])
        with col4:
            st.metric("% ejecutado", piv_entidad.loc[8, "perc_ejecucion"])
        with col5:
            st.metric("% comprometido", piv_entidad.loc[8, "perc_compr"])

        mean_growth_rate = (piv_entidad.loc[8, "perc_ejecucion"] / 8) / 100

        # Step 2: Forecast the next 4 values
        last_value = piv_entidad['perc_ejecucion'].iloc[-1]
        forecast_values = [mean_growth_rate * i * 100 for i in range(9, 13)]

        # Combine original and forecasted values
        full_values = piv_entidad['perc_ejecucion'].tolist() + forecast_values
        full_values = [round(i, 1) for i in full_values]

        # Step 3: Create a line plot
        fig = make_subplots(rows=1, cols=2, subplot_titles=("Ejecutado (%)", "Comprometido (%)"))

        # Plot the first 8 values (blue solid line)
        fig.add_trace(go.Scatter(
            x=months[:9],  # x-axis for all values (1 to 12)
            y=full_values[:9],         # All values (original + forecast)
            mode='lines+markers',  # Line and markers
            name='Observado', showlegend=False,
            line=dict(color='#2635bf', width=2),  # Solid blue line for all values
            marker=dict(color=['#2635bf']*9, size=8)  # Red markers for forecasted values
        ), row=1, col=1)

        # Highlight the forecasted part with a red dashed line (the last 4 points)
        fig.add_trace(go.Scatter(
            x=months[8:],  # x-axis for forecasted values
            y=full_values[8:],     # The forecasted values
            mode='lines+markers',          # Just lines (no markers here)
            name='Pronóstico', showlegend=False,
            line=dict(color='#dd722a', width=2, dash='dash'),
            marker=dict(color='#dd722a', size=8),  # Dashed line for forecast
        ), row=1, col=1)

        mean_growth_rate = (piv_entidad.loc[8, "perc_compr"] / 8) / 100

        # Step 2: Forecast the next 4 values
        last_value = piv_entidad['perc_compr'].iloc[-1]
        forecast_values = [mean_growth_rate * i * 100 for i in range(9, 13)]

        # Combine original and forecasted values
        full_values = piv_entidad['perc_compr'].tolist() + forecast_values
        full_values = [round(i, 1) for i in full_values]

        fig.add_trace(go.Scatter(
            x=months[:9],  # x-axis for all values (1 to 12)
            y=full_values[:9],         # All values (original + forecast)
            mode='lines+markers',  # Line and markers
            name='Observado', showlegend=True,
            line=dict(color='#2635bf', width=2),  # Solid blue line for all values
            marker=dict(color=['#2635bf']*9, size=8)  # Red markers for forecasted values
        ), row=1, col=2)



        # Highlight the forecasted part with a red dashed line (the last 4 points)
        fig.add_trace(go.Scatter(
            x=months[8:],  # x-axis for forecasted values
            y=full_values[8:],     # The forecasted values
            mode='lines+markers',          # Just lines (no markers here)
            name='Pronóstico', showlegend=True,
            line=dict(color='#dd722a', width=2, dash='dash'),
            marker=dict(color='#dd722a', size=8),  # Dashed line for forecast
        ), row=1, col=2)

        fig.add_shape(type='line', x0=0, x1=11, y0=100, y1=100, line=dict(color='#2635bf', dash='dash'),
                    row=1, col=2)
        fig.add_shape(type='line', x0=0, x1=11, y0=100, y1=100, line=dict(color='#2635bf', dash='dash'),
                    row=1, col=1)
        fig.update_yaxes(range=[0, max(100, max(full_values))]) 

        fig.update_layout(
            title=f"Ejecución y compromiso al mes de agosto por entidad: {entidad}",
            height=400, 
            width=900,
            legend=dict(
                orientation='h',
                yanchor="bottom",
                y=1.1,
                xanchor="right",
                x=1 # Align the legend vertically
            )
        )

        # Show the plot
        st.plotly_chart(fig)

        perd_aprop = 100 - full_values[-1]

        if perd_aprop > 0:
            st.error(f"Hay una pérdida de apropiación del {round(perd_aprop, 2)}% para la entidad {entidad}.")
        else:
            st.success(f"No hay pérdida de apropiación para la entidad {entidad}.")

    with tab3:
        st.subheader("Descarga de datos")

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
                    label="Descargar CSV",
                    data=csv,
                    file_name='datos_ejecucion_agosto.csv',
                    mime='text/csv')

elif selected_option == 'Recaudo':
    rec = pd.read_csv('datasets/recaudo.csv')
    rec['Valor'] = rec['Valor'] / 1_000

    tab1, tab2, tab3 = st.tabs(['General', 'Interno', 'Externo'])

    with tab1:
        piv_year = rec.groupby(['Mes_num', 'Mes'])['Valor'].sum().reset_index()
        acum = (piv_year
                                        .groupby(['Mes_num', 'Mes'])['Valor']
                                        .sum()
                                        .reset_index()
                                        .assign(Acumulado=lambda x: x['Valor'].cumsum()))[['Mes','Acumulado']]
        fig = make_subplots(rows=1, cols=2, x_title='Año',  )
        
        fig.add_trace(
                go.Scatter(
                x=acum['Mes'],  # x-axis for forecasted values
                y=acum['Acumulado'],     # The forecasted values
                mode='lines+markers',          # Just lines (no markers here)
                name='Recaudo acumulado', showlegend=True,
                line=dict(color=DIC_COLORES['ax_viol'][1], width=2, dash='dash'),
                marker=dict(color=DIC_COLORES['ax_viol'][1], size=8),  # Dashed line for forecast
            ), row=1, col=1
            )

        piv_recaudo = (rec
                        .groupby(['Mes_num','Mes', 'Tipo de impuesto'])['Valor']
                        .sum()
                        .reset_index())
        piv_recaudo['total'] = piv_recaudo.groupby(['Mes_num'])['Valor'].transform('sum')

        piv_recaudo['%'] = ((piv_recaudo['Valor'] / piv_recaudo['total']) * 100).round(2)
        dict_rec = {'Interno':DIC_COLORES['az_verd'][2],
              'Externo':DIC_COLORES['ax_viol'][1],
              'Por clasificar':DIC_COLORES['ro_am_na'][3]}

        for i, group in piv_recaudo.groupby('Tipo de impuesto'):
            fig.add_trace(go.Bar(
                x=group['Mes'],
                y=group['%'],
                name=i, marker_color=dict_rec[i],
            ),  row=1, col=2)


        fig.update_layout(barmode='stack', hovermode='x unified')
        fig.update_layout(width=1000, height=500, legend=dict(orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1), title='Histórico general <br><sup>Cifras en miles de millones de pesos</sup>', yaxis_tickformat='.0f')


        st.plotly_chart(fig)  

         
    with tab2:
            rec_int = rec[rec['Tipo de impuesto'] == 'Interno']
            piv_recaudo = (rec_int
                            .groupby(['Mes_num','Mes', 'clas_alt'])['Valor']
                            .sum()
                            .reset_index())
            acum = (piv_recaudo
                                        .groupby(['Mes_num', 'Mes'])['Valor']
                                        .sum()
                                        .reset_index()
                                        .assign(Acumulado=lambda x: x['Valor'].cumsum()))[['Mes','Acumulado']]
            piv_recaudo['total'] = piv_recaudo.groupby(['Mes_num'])['Valor'].transform('sum')

            piv_recaudo['%'] = ((piv_recaudo['Valor'] / piv_recaudo['total']) * 100).round(2)
            fig = make_subplots(rows=1, cols=2, x_title='Año',  )
        
            fig.add_trace(
                go.Scatter(
                x=acum['Mes'],  # x-axis for forecasted values
                y=acum['Acumulado'],     # The forecasted values
                mode='lines+markers',          # Just lines (no markers here)
                name='Recaudo acumulado', showlegend=True,
                line=dict(color=DIC_COLORES['ax_viol'][1], width=2, dash='dash'),
                marker=dict(color=DIC_COLORES['ax_viol'][1], size=8),  # Dashed line for forecast
            ), row=1, col=1
            )
            dict_alt = {'IVA Interno':DIC_COLORES['az_verd'][2],
              'Renta':DIC_COLORES['ax_viol'][1],
              'Otros':DIC_COLORES['ro_am_na'][3]}

            for i, group in piv_recaudo.groupby('clas_alt'):
                fig.add_trace(go.Bar(
                    x=group['Mes'],
                    y=group['%'],
                    name=i, marker_color=dict_alt[i]
                ),  row=1, col=2)


            fig.update_layout(barmode='stack', hovermode='x unified')
            fig.update_layout(width=1000, height=500, legend=dict(orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1), title='Histórico interno <br><sup>Cifras en miles de millones de pesos</sup>', yaxis_tickformat='.0f')


            st.plotly_chart(fig)

    with tab3:
            rec_ext = rec[rec['Tipo de impuesto'] == 'Externo']
            piv_recaudo = (rec_ext
                            .groupby(['Mes_num','Mes', 'Clasificación'])['Valor']
                            .sum()
                            .reset_index())
            acum = (piv_recaudo
                                        .groupby(['Mes_num', 'Mes'])['Valor']
                                        .sum()
                                        .reset_index()
                                        .assign(Acumulado=lambda x: x['Valor'].cumsum()))[['Mes','Acumulado']]
            piv_recaudo['total'] = piv_recaudo.groupby(['Mes_num'])['Valor'].transform('sum')

            piv_recaudo['%'] = ((piv_recaudo['Valor'] / piv_recaudo['total']) * 100).round(2)
            fig = make_subplots(rows=1, cols=2, x_title='Año',  )
        
            fig.add_trace(
                go.Scatter(
                x=acum['Mes'],  # x-axis for forecasted values
                y=acum['Acumulado'],     # The forecasted values
                mode='lines+markers',          # Just lines (no markers here)
                name='Recaudo acumulado', showlegend=True,
                line=dict(color=DIC_COLORES['ax_viol'][1], width=2, dash='dash'),
                marker=dict(color=DIC_COLORES['ax_viol'][1], size=8),  # Dashed line for forecast
            ), row=1, col=1
            )
            dict_alt = {'IVA Externo ':DIC_COLORES['ro_am_na'][3],
              'Arancel':DIC_COLORES['az_verd'][2]}
            for i, group in piv_recaudo.groupby('Clasificación'):
                fig.add_trace(go.Bar(
                    x=group['Mes'],
                    y=group['%'],
                    name=i, marker_color=dict_alt[i]
                ),  row=1, col=2)


            fig.update_layout(barmode='stack', hovermode='x unified')
            fig.update_layout(width=1000, height=500, legend=dict(orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1), title='Histórico externo <br><sup>Cifras en miles de millones de pesos</sup>', yaxis_tickformat='.0f')


            st.plotly_chart(fig)
        


elif selected_option == "Proyecto - 2025":

    st.header("Proyecto de ley - 2025")
    df2025['TOTAL_mil'] = (df2025['TOTAL'] / 1000000).round(1)

    fig = px.treemap(df2025, path=[px.Constant('Proyecto'), 'Sector', 'Entidad', 'Tipo de gasto'],
                            values='TOTAL_mil',
                            title="Matriz de composición anual del proyecto <br><sup>Cifras en millones de pesos</sup>",
                            color_continuous_scale='Teal')

    fig.update_layout(width=1000, height=600)
            
    st.plotly_chart(fig)

    st.subheader("Descarga de datos")


    binary_output = BytesIO()
    df2025.to_excel(binary_output, index=False)
    st.download_button(label = 'Descargar datos de proyecto',
                    data = binary_output.getvalue(),
                    file_name = 'proyecto_2025.xlsx')  

    
    
    st.header("Anteproyecto - 2025")

    df4 = df2.copy()
    df4.loc[df4['CTA PROG'].isna(), 'CTA PROG'] = 'Inversión'

    fig = px.treemap(df4, 
                            path=[px.Constant('Anteproyecto'), 'Sector', 'Entidad','Tipo de gasto', 
                                    'CTA PROG'],
                            values='Apropiación 2025',
                            title="Matriz de composición anual del Anteproyecto <br><sup>Cifras en millones de pesos</sup>",
                            color_continuous_scale='Teal')
            
    fig.update_layout(width=1000, height=600)
            
    st.plotly_chart(fig)

    st.subheader("Flujo del gasto por tipo de gasto (% del PGN)")

    lista = ['PGN', 'Tipo de gasto', 'CTA PROG']
    df3 = df2.copy()
    df3['PGN'] = 'PGN'

    dicti = {'2':['Inversión','Deuda']}
    nodes, rev_info, links = create_dataframe_sankey(df3, '% porc',*lista, **dicti)
    fig = go.Figure(data=[go.Sankey(
    arrangement='snap',
    node = dict(
      pad = 15,
      thickness = 20,
      line = dict(color = "#2635bf", width = 0.5),
      label = nodes['names'],
      color = nodes['color'],
      x = nodes['x_pos'].values ,
      y = nodes['x_pos'].values / 2.4
    ),
    link = dict(
      source = links['source'], 
      target = links['target'],
      value = links['value'],
      color = links['color'],
      hovertemplate='Proporción del gasto de %{source.label}<br />'+
        'hacia %{target.label}:<br /> <b>%{value:.2f}%<extra></extra>'
    ))])

    fig.update_layout(title_text="Flujo del gasto", 
                      font_size=12, 
                      width=1000, 
                      height=600)
    st.plotly_chart(fig)




    st.subheader("Flujo del gasto por sector (% del PGN)")
    lista = ['PGN', 'Sector', 'Tipo de gasto', 'CTA PROG']
    df3 = df2.copy()
    df3['PGN'] = 'PGN'

    top_10 = df2.groupby('Sector')['Apropiación 2025'].sum().reset_index().sort_values(by='Apropiación 2025', ascending=False).head(10)['Sector']

    df3.loc[~df3['Sector'].isin(top_10), 'Sector'] = 'Otros sectores'

    dicti = {'3':['Inversión','Deuda']}
    nodes, rev_info, links = create_dataframe_sankey(df3, '% porc',*lista, **dicti)
    fig = go.Figure(data=[go.Sankey(
    arrangement='snap',
    node = dict(
      pad = 15,
      thickness = 20,
      line = dict(color = "#2635bf", width = 0.5),
      label = nodes['names'],
      color = nodes['color'],
      x = nodes['x_pos'].values ,
      y = nodes['x_pos'].values / 2.4
    ),
    link = dict(
      source = links['source'], 
      target = links['target'],
      value = links['value'],
      color = links['color'],
      hovertemplate='Proporción del gasto de %{source.label}<br />'+
        'hacia %{target.label}:<br /> <b>%{value:.2f}%<extra></extra>'
    ))])

    fig.update_layout(title_text="Flujo del gasto por sector", 
                      font_size=12, 
                      width=1000, 
                      height=600)
    st.plotly_chart(fig)
    

    st.subheader("Flujo del gasto por entidad (% del PGN)")
    lista = ['PGN','Entidad', 'Tipo de gasto', 'CTA PROG']
    df3 = df2.copy()
    df3['PGN'] = 'PGN'

    top_10 = df2.groupby('Entidad')['Apropiación 2025'].sum().reset_index().sort_values(by='Apropiación 2025', ascending=False).head(10)['Entidad']

    df3.loc[~df3['Entidad'].isin(top_10), 'Entidad'] = 'Otras entidades'

    dicti = {'3':['Inversión','Deuda']}
    nodes, rev_info, links = create_dataframe_sankey(df3, '% porc',*lista, **dicti)
    fig = go.Figure(data=[go.Sankey(
    arrangement='snap',
    node = dict(
      pad = 15,
      thickness = 20,
      line = dict(color = "#2635bf", width = 0.5),
      label = nodes['names'],
      color = nodes['color'],
      x = nodes['x_pos'].values,
      y = nodes['x_pos'].values / 2.4
    ),
    link = dict(
      source = links['source'], 
      target = links['target'],
      value = links['value'],
      color = links['color'],
      hovertemplate='Proporción del gasto de %{source.label}<br />'+
        'hacia %{target.label}:<br /> <b>%{value:.2f}%<extra></extra>'
    ))])

    fig.update_layout(title_text="Flujo del gasto por entidad", 
                      font_size=12, 
                      width=1000, 
                      height=600)
    st.plotly_chart(fig)

    st.subheader("Descarga de datos")


    binary_output = BytesIO()
    df2.to_excel(binary_output, index=False)
    st.download_button(label = 'Descargar datos de anteproyecto',
                    data = binary_output.getvalue(),
                    file_name = 'anteproyecto_2025.xlsx')    

    

else:
    st.header("Descarga de datos")

    st.subheader("Descarga de dataset completo")


    binary_output = BytesIO()
    df.to_excel(binary_output, index=False)
    st.download_button(label = 'Descargar datos completos',
                    data = binary_output.getvalue(),
                    file_name = 'datos.xlsx')

    st.subheader("Descarga de dataset filtrado")
    col1, col2 = st.columns(2)
    with col1:
        sectors_2 = ['Todos'] + sectors
        sectors_selected = st.multiselect("Sector(es)", sectors_2)
        if "Todos" in sectors_selected:
            filter_ss = df[df['Sector'].isin(sectors)]
        else:
            filter_ss = df[df['Sector'].isin(sectors_selected)]


        entities_2 = ['Todas'] + list(filter_ss['Entidad'].unique())

        entities_selected = st.multiselect("Entidad(es)", entities_2)

        if "Todas" in entities_selected:
            entities_selected = list(filter_ss['Entidad'].unique())
        #rango de años
        years_2 = ['Todos'] + years
        years_selected = st.multiselect("Año(s)", years_2)

        if "Todos" in years_selected:
            years_selected = years.copy()

        filter_s_e_y = filter_ss[(filter_ss['Entidad'].isin(entities_selected)) & (filter_ss['Año'].isin(years_selected))]

    with col2:

        price_selected = st.selectbox("Nivel(es) de precios", prices.keys())
        total_or_account = st.selectbox("Suma o por cuenta", ["suma", "por cuenta"])
        if total_or_account == 'suma':
            pivot = (filter_s_e_y.groupby(['Año', 
                                          'Sector',
                                          'Entidad'])[prices[price_selected]]
                                          .sum()
                                          .reset_index())
        
        else:
            pivot = (filter_s_e_y.groupby(['Año', 
                                          'Sector',
                                          'Entidad','Tipo de gasto'])[prices[price_selected]]
                                          .sum()
                                          .reset_index())
        if st.button('Vista previa'):
            show = True            
            
    if show:
        st.dataframe(pivot)
        csv = convert_df(pivot)

        st.download_button(
                label="Descargar CSV",
                data=csv,
                file_name='datos.csv',
                mime='text/csv')
        
        binary_output = BytesIO()
        pivot.to_excel(binary_output, index=False)
        st.download_button(label = 'Descargar excel',
                    data = binary_output.getvalue(),
                    file_name = 'datos.xlsx')
        
    st.divider()
        
    st.subheader("Descarga del árbol sector-entidad del PGN")
    with open('dictios/dictio.json', 'rb') as js:
        dictio = json.load(js)

    json_string = json.dumps(dictio)
    st.json(json_string, expanded=False)

    st.download_button(
        label='Descargar JSON',
        file_name='dictio.json',
        mime="application/json",
        data=json_string
    )





   
