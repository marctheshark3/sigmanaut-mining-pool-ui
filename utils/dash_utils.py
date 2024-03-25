from utils.reader import SigmaWalletReader, PriceReader
from dash import Dash, html, dash_table, dcc
import dash_bootstrap_components as dbc

import pandas as pd
import plotly.express as px
from dash.dependencies import Input, Output
import plotly.graph_objs as go

dark_theme_table_style = {} #{'overflowX': 'auto', 'padding': '10px'}

dark_theme_style_header = {'backgroundColor': '#222', 'color': '#FFFFFF', 'fontWeight': 'bold', 'textAlign': 'left'}

dark_theme_style_cell = {'backgroundColor': '#333', 'color': '#FFFFFF', 'textAlign': 'left', 'padding': '10px',}

container_style = {'flex': 1, 'margin': '10px', 'padding': '10px', 'border': 'none', 'borderRadius': '5px', 'background': '#1e1e1e'}

card_style = {
    'backgroundColor': '#333333',
    'color': 'white',
    'marginBottom': '25px',
    'padding': '25px',
    'justifyContent': 'center',
}

metric_row_style = {
    'display': 'flex',
    'alignItems': 'center',
    'justifyContent': 'flex-start',
}

image_style = {'height': '75px', 'padding': '10px'}
# def create_row_card(h2_text, p_text, image=None):
#     if image:
#         children = html.Img(src=image, style=image_style)
#     else:
#         children = []
#     children.append(html.H2(h2_text, style={'color': '#FFA500'}))
#     children.append(html.P(p_text))

#     return dbc.Col(dbc.Card(style=card_style, children=[children]), style={'marginRight': 'auto', 'marginLeft': 'auto'})

def create_row_card(h2_text, p_text, image=None):
    return dbc.Col(dbc.Card(style=card_style, children=[
        # html.Img(src=image, style=top_image_style),
        html.H2(h2_text, style={'color': '#FFA500'}),
        html.P(p_text)]),
                   style={'marginRight': 'auto', 'marginLeft': 'auto'})

def create_image_text_block(text, image=None):
    if image:
        return html.Div(style=metric_row_style, children=[
                        html.Img(src='assets/{}'.format(image), style=image_style),
                        html.Span(text, style={'padding': '10px'})])
    else:
        return html.Div(style=metric_row_style, children=[
                        # html.Img(src='assets/{}'.format(image), style=image_style),
                        html.Span(text, style={'padding': '10px'})])
    

def create_pie_chart(df, col, value, est_reward=False):
    if est_reward:
        chart = go.Figure(data=[go.Pie(labels=df[col], values=df[value], textinfo='value',
                               insidetextorientation='radial')], layout=go.Layout())
    else:
        chart = px.pie(df, names=col, values=value, color=col)
    pulls = [0.1 if item else 0 for item in df['my_wallet']]
    chart.update_traces(pull=pulls)
    chart.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                        font_color='white', title_font_color='white', legend_title_font_color='white',
                        xaxis=dict(title_font_color='white', tickfont_color='white', gridcolor='grey'),
                        yaxis=dict(title_font_color='white', tickfont_color='white', gridcolor='grey'))
    chart.update_layout(margin=dict(t=0, b=0, l=0, r=0),autosize=False, width=350, height=350)
    return chart
    
def create_bar_chart(df, x, y, color, labels=None):
    chart = px.bar(df, x=x, y=y, color=color, labels=labels,
                  color_continuous_scale=px.colors.sequential.Viridis)
    chart.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                        font_color='white', title_font_color='white', legend_title_font_color='white',
                        xaxis=dict(title_font_color='white', tickfont_color='white', gridcolor='grey'),
                        yaxis=dict(title_font_color='white', tickfont_color='white', gridcolor='grey'))

    return chart

def create_table_component(title, data_table_id, columns, data, max_table_width='none'):
    # Apply max width to the table container
    custom_table_style = {**dark_theme_table_style, 'maxWidth': max_table_width}

    return html.Div([
        html.H2(title,),
        dash_table.DataTable(
            id=data_table_id,
            columns=[{"name": i, "id": i} for i in columns],
            data=data.to_dict('records'),
            style_data={'border': 'none'},
            style_table=custom_table_style,
            style_header=dark_theme_style_header,
            style_cell=dark_theme_style_cell,
            style_as_list_view=True, 
        ),
    ], style=container_style)