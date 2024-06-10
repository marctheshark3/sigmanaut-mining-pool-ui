import dash
from dash import dcc, html
from dash.dependencies import Input, Output

app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Location(id='url', refresh=True),  # Component to handle URL redirection
    html.H1('Mint NFT'),
    html.Button('Mint NFT', id='mint-button', n_clicks=0),
])

@app.callback(
    Output('url', 'href'),
    [Input('mint-button', 'n_clicks')]
)
def mint_nft(n_clicks):
    if n_clicks > 0:
        return 'http://localhost:3000/mintNFT'
    # return ''

if __name__ == '__main__':
    app.run_server(debug=True)
