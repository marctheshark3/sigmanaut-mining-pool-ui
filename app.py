from utils.reader import SigmaWalletReader
from dash import Dash, html, dash_table, dcc
import dash_bootstrap_components as dbc

import pandas as pd
import plotly.express as px
from dash.dependencies import Input, Output
import plotly.graph_objs as go

sigma_reader = SigmaWalletReader(config_path="../conf")

# Fetch data using SigmaWalletReader instance
mining_df, performance_df = sigma_reader.get_mining_stats()
block_df, miner_df, effort_df = sigma_reader.get_block_stats()
pool_df, top_miner_df = sigma_reader.get_pool_stats()

mining_data_df = pd.concat([mining_df, effort_df])
top_miner_df_sorted = top_miner_df.sort_values(by='hashrate', ascending=True)

block_df['created'] = pd.to_datetime(block_df['created'])

# Create bar charts
miner_chart = px.bar(miner_df, y='Miner', x='Number of Blocks Found', title='Number of Blocks Found by Miner',
                    color='my_wallet',  # This will automatically assign different colors
                    color_discrete_map={True: 'blue', False: 'red'})  # Custom colors for True/False)

top_miner_chart = px.bar(top_miner_df_sorted, y='miner', x='hashrate', title='Top Miners by Shares',
                         color='my_wallet',  # This will automatically assign different colors
                         color_discrete_map={True: 'blue', False: 'red'}
                        )  # Custom colors for True/False)

effort_chart = px.bar(block_df, x='created', y='effort', color='networkDifficulty',
                      title='Block Effort Over Time',
                      labels={'created': 'Block Creation Date', 'effort': 'Effort', 'networkDifficulty': 'Network Difficulty'},
                      color_continuous_scale=px.colors.sequential.Viridis)

my_wallet_blocks = block_df[block_df['my_wallet']]

effort_chart.add_trace(go.Scatter(
    x=my_wallet_blocks['created'],
    y=my_wallet_blocks['effort'],
    mode='markers',
    marker=dict(
        color='Red',  # Sets the color of the markers
        size=10,  # Sets the size of the markers
        symbol='circle'  # Sets the shape of the markers
    ),
    name='My Wallet'
))

effort_chart.update_layout(
    title='Effort and My Wallet Blocks',
    xaxis_title='Creation Date',
    yaxis_title='Effort',
    legend_title='Legend',
    coloraxis=dict(colorscale='Viridis'),  # Color scale for the bar colors
    legend=dict(
        yanchor="top",
        y=0.99,  # Adjusts vertical position; 1.0 is top, 0 is bottom
        xanchor="right",
        x=0.99 ) # Adjusts horizontal position; 1.0 is right, 0 is left
)
charts = [miner_chart, top_miner_chart, effort_chart]
for chart in charts:
    chart.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',  # Transparent background
        paper_bgcolor='rgba(0,0,0,0)',  # Transparent surrounding
        font_color='white',  # Light text suitable for dark backgrounds
        title_font_color='white',  # Ensure title is visible
        legend_title_font_color='white',  # Ensure legend title is visible
        xaxis=dict(
            title_font_color='white',
            tickfont_color='white',
            gridcolor='grey'  # Lighter grid lines for visibility
        ),
        yaxis=dict(
            title_font_color='white',
            tickfont_color='white',
            gridcolor='grey'
        )
    )

style_table_container = {'flex': '1 1 auto', 'minWidth': '250px',
                         'overflowX': 'auto', 'overflowY': 'auto',
                         'backgroundColor': 'rgb(30, 30, 30)',
                         'color': 'white'}

# Initialize the Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

# Define the layout of the app
app.layout = html.Div(children=[
    html.H1(children='Sigma Mining Pool Dashboard'),

    # Container for tables in the same row
    html.Div(children=[
        # Mining Statistics Table with flex styling
        html.Div(children=[
            html.H2('Payment Stats'),
            dash_table.DataTable(
                id='mining-stats',
                columns=[{"name": i, "id": i} for i in mining_data_df.columns],
                data=mining_data_df.to_dict('records'),
                style_table=style_table_container,
                style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white'},
                style_cell={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white', 'minWidth': '150px', 'width': '150px', 'maxWidth': '150px'},  # Ensure cells have enough space
                style_as_list_view=True,  # Optional, for aesthetics
            ),
        ], style={'flex': 1}),  # Adjust flex value as needed for sizing

        # Performance Statistics Table with flex styling
        html.Div(children=[
            html.H2('Your Performance Stats'),
            dash_table.DataTable(
                id='performance-stats',
                columns=[{"name": i, "id": i} for i in performance_df.columns],
                data=performance_df.to_dict('records'),
                style_table=style_table_container,
                style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white'},
                style_cell={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white',},
                
            ),
        ], style={'flex': 1}),  # Adjust flex value as needed for sizing

        # Pool and Network Statistics Table with flex styling
        html.Div(children=[
            html.H2('Pool and Network Stats'),
            dash_table.DataTable(
                id='pool-stats',
                columns=[{"name": i, "id": i} for i in pool_df.columns],
                data=pool_df.to_dict('records'),
                style_table=style_table_container,
                style_cell={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white',},
                style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white'},
            ),
        ], style={'flex': 1}),  # Adjust flex value as needed for sizing
        
    ], style={'display': 'flex', 'flexDirection': 'row', 'gap': '20px', 'flexWrap': 'nowrap', 'overflowX': 'auto'}),

    # Container for charts in the same row
    html.Div(children=[
        # Blocks Found by Miner Chart
        html.Div(children=[
            html.H2('Blocks Found by Miner'),
            dcc.Graph(
                id='miner-chart',
                figure=miner_chart
            ),
        ], style={'flex': 1}),  # Adjust flex value as needed for sizing

        # Top Miners by Shares Chart
        html.Div(children=[
            html.H2('Top Miners by Shares'),
            dcc.Graph(
                id='top-miner-chart',
                figure=top_miner_chart
            ),
        ], style={'flex': 1}),  # Adjust flex value as needed for sizing
    ], style={'display': 'flex', 'flexDirection': 'row', 'gap': '20px'}),

    html.Div(children=[
        html.H2('Block Effort Over Time'),
        dcc.Graph(
            id='effort-chart',
            figure=effort_chart
        )
    ], style={'margin-top': '20px'}),

    # Block Statistics and Average Effort Tables
    html.Div(children=[
        html.H2('Block Statistics'),
        dash_table.DataTable(
            id='block-stats',
            columns=[{"name": i, "id": i} for i in block_df.columns],
            data=block_df.to_dict('records'),
            style_table={'height': '300px', 'overflowY': 'auto'},
            style_cell={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white',},
            style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white'},
            
        ),
        
    ]),
])

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)