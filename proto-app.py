import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
from utils.find_miner_id import ReadTokens

reader = ReadTokens()

miner_swap_data = reader.get_api_data('http://5.78.102.130:8000/miningcore/swap_payments/9f4WEgtBoWrtMa4HoUmxA3NSeWMU9PZRvArVGrSS3whSWfGDBoY')

# Assume miner_swap_data is your provided JSON data
# Convert it to a pandas DataFrame


df = pd.DataFrame(miner_swap_data)

# Convert timestamp to datetime
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Create the Dash app
app = dash.Dash(__name__)

# Define the layout
app.layout = html.Div([
    html.H1("Miner Swap Data Dashboard"),
    
    # Summary Table
    html.H2("Summary Table"),
    dash_table.DataTable(
        id='summary-table',
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict('records'),
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left'},
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold'
        },
        page_size=10
    ),
    
  
])

if __name__ == '__main__':
    app.run_server(debug=True)