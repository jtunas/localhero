# -*- coding: utf-8 -*-
"""
Created on Thu Apr 16 18:38:39 2020

@author: Johnny
"""
import plotly.graph_objects as go
from dash.dependencies import Input, Output,State
from dash.exceptions import PreventUpdate
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd

raw_data = pd.read_csv(
    'https://raw.githubusercontent.com/jtunas/localhero/master/data.csv', sep = ';',
    dtype=object,
)

mapbox_access_token = "pk.eyJ1IjoicGxvdGx5bWFwYm94IiwiYSI6ImNqdnBvNDMyaTAxYzkzeW5ubWdpZ2VjbmMifQ.TXcBE-xg9BFdV2ocecc_7g"

app = dash.Dash(
    __name__, 
    external_stylesheets=[dbc.themes.SPACELAB],
    #suppress_callback_exceptions = True
    )

def get_local_products(df, local_name):
    local_df = df.query('name in @local_name')
    return [html.Div(i) for i in local_df['producto'].unique()]

def get_local_servicio_domicilio(df, local_name):
    local_df = df.query('name in @local_name')
    exists_servicio_domicilio = local_df['servicio_domicilio'].unique() != "No disponible"
    if exists_servicio_domicilio:
        return [html.A(i, href=i, target="_blank") for i in local_df['servicio_domicilio'].unique()]
    return [html.P(local_df['servicio_domicilio'].unique())]

def get_local_bonos(df, local_name):
    local_df = df.query('name in @local_name')
    exists_bonos = local_df['bonos'].unique() != "No disponible"
    if exists_bonos:
        return [html.A(i, href=i, target="_blank") for i in local_df['bonos'].unique()]    
    return [html.P(local_df['bonos'].unique())]

def local_modal():
    return html.Div(
        dbc.Modal(
            [
                dbc.ModalHeader(id = "local_modal-header"),
                dbc.ModalBody(id = "local_modal-body"),
                dbc.ModalFooter(id = "local_modal-footer", 
                                children = [
                                                html.Div([
                                                    html.H6("A domicilio: "),
                                                    html.Div(id = "link-serv-domicilio-local")
                                                    ],style = {'position' : 'absolute', 'left' : '7px',
                                                                   'margin-top' : '4px'}),
                                                html.Div([
                                                    html.H6("Apadrina el negocio en: "), 
                                                    html.Div(id="navlink-bonos-local")
                                                    ],)
                                          ]),
            ],
            id="local_modal",
        ),
    )

def mapa_plot():
    return html.Div(dcc.Graph(id="mapa",
                         config={'displayModeBar': False,
                                  'scrollZoom': True},
                         style={"height":"800px"}),)

def search_bar():
    return html.Div(id = 'search-bar', 
                    children= [
                        dbc.Row([
                            dbc.Col(width = 4),
                            dbc.Col(
                                dbc.Input(
                                    id="search_input",
                                    type="search",
                                    placeholder="Busca lo que deseas",
                                ), width = 4, className = "mr-2"),
                            dbc.Col(width = 4),
                            ])
                        ], 
                    style= {'z-index': '20', 'position':'fixed', 'width':'100%', 'margin-top': '20px'})
                            
content =  html.Div(
    id="page-content",
    children = [search_bar(), mapa_plot(), local_modal()],
    style = {  'position': 'relative'}
    )

app.layout = html.Div([content])

@app.callback(
    [Output("local_modal", "is_open"),
     Output("local_modal-header", "children"),
     Output("local_modal-body", "children"),
     Output("link-serv-domicilio-local", "children"),     
     Output("navlink-bonos-local", "children"),
     ],
    [Input('mapa', 'clickData')],
)
def toggle_local_modal(clicked_data_from_map):
    if not clicked_data_from_map:
         raise PreventUpdate
    selectedLocalName = clicked_data_from_map['points'][0]['text'] 
    products = get_local_products(raw_data, selectedLocalName)
    servicio_domicilio = get_local_servicio_domicilio(raw_data, selectedLocalName)
    bonos = get_local_bonos(raw_data, selectedLocalName)
    return True, selectedLocalName, products, servicio_domicilio, bonos

@app.callback(
        Output("mapa", "figure"),
        [Input("local_modal","is_open"),
         Input("search_input", "value")]
    )
def update_graph(unuseful, search):
        # Data preparation
        zoom = 16.0
        latInitial = 40.54749;
        lonInitial = -4.181604
        bearing = 0
        if search:
            df = raw_data.query('producto in @search')
        else:
            df = raw_data
        return go.Figure(
            data=[
                # Data for all rides based on date and time
                go.Scattermapbox(
                    lat=df["lat"],
                    lon=df["long"],
                    mode="markers+text",
                    hoverinfo="text",
                    text=df['name'],
                    textposition="top center",
                    marker=dict(
                        size=15,
                        symbol = df["symbol"],
                    ),
                ),
            ],
            layout=go.Layout(
                autosize=True,
                margin=go.layout.Margin(l=1, r=1, t=0, b=0),
                showlegend=False,
                 clickmode='event+select',
                mapbox=dict(
                    accesstoken=mapbox_access_token,
                    center=dict(lat=latInitial, lon=lonInitial),
                    style="streets",
                    bearing=bearing,
                    zoom=zoom,
                ),
                updatemenus=[
                    dict(
                        buttons=(
                            [
                                dict(
                                    args=[
                                        {
                                            "mapbox.zoom": zoom,
                                            "mapbox.center.lon": lonInitial,
                                            "mapbox.center.lat": latInitial,
                                            "mapbox.bearing": bearing,
                                            "mapbox.style": "streets",
                                        }
                                    ],
                                    label="Reset Zoom",
                                    method="relayout",
                                )
                            ]
                        ),
                        direction="left",
                        pad={"r": 0, "t": 0, "b": 0, "l": 0},
                        showactive=False,
                        type="buttons",
                        x=0.45,
                        y=0.02,
                        xanchor="left",
                        yanchor="bottom",
                        bgcolor="#323130",
                        borderwidth=1,
                        bordercolor="#6d6d6d",
                        font=dict(color="#FFFFFF"),
                    )
                ],
            ),
        )
    
server = app.server
   
if __name__ == "__main__":
    app.run_server(debug = False)