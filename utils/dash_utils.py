from dash import html, dash_table, dcc
import dash_bootstrap_components as dbc
from typing import Dict

# Colors
card_color = '#27374D'
background_color = '#526D82'
large_text_color = '#9DB2BF'
small_text_color = '#DDE6ED'


top_image_style = {
    'height': '150px',
    'width': '150px',
                   'justifyContent': 'center',}

# Card Styles
card_styles = {
    'stat_card': {
        'backgroundColor': card_color,
        'padding': '15px',
        'margin': '8px',
        'borderRadius': '8px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
    },
    'metric_card': {
        'backgroundColor': card_color,
        'padding': '15px',  # Reduced padding
        'margin': '5px',    # Reduced margin
        'borderRadius': '8px',
        'height': '180px',  # Fixed height for consistency
        'display': 'flex',
        'flexDirection': 'column',
        'justifyContent': 'space-between'
    }
}

# Table Styles
table_style = {
    'backgroundColor': card_color,
    'color': large_text_color,
    'fontWeight': 'bold',
    'textAlign': 'center',
    'border': '1px solid black',
    'padding': '15px',
    'letterSpacing': '0.02em',
    'lineHeight': '1.4'
}

top_card_style = {
    'backgroundColor': card_color,
    'padding': '15px',
    'height': 'auto',  # Fixed height for first row cards
    # 'display': 'flex',
    # 'flexDirection': 'column',
    'alignItems': 'center',
    # 'justifyContent': 'space-between',
    # 'borderRadius': '8px',
}

# First row text styles
first_row_styles = {
    'value': {
        'color': '#ff5e18',
        'fontSize': '24px',
        'fontWeight': 'bold',
        'marginTop': '10px',
        'marginBottom': '5px'
    },
    'label': {
        'color': small_text_color,
        'fontSize': '14px',
    }
}


# Row Styles
top_row_style = {
    'backgroundColor': card_color,
    'color': 'white',
    'display': 'flex',
    'padding': '20px',
    'height': 'auto',
    'justifyContent': 'flex-start',
}

# Bottom card styles
bottom_row_style = {
    'backgroundColor': card_color,
    'color': 'white',
    # 'padding': '12px 15px',  # Reduced padding
    # 'display': 'flex',
    'alignItems': 'flex-start',
    'justifyContent': 'left',
    'fontSize': '14px',
    'borderRadius': '6px',
    'margin': '5px 0',      # Added small margin between rows
}

image_styles = {
    'standard': {'height': '40px'},
    'bottom': {
        'height': '75px',
        'width': '75px',
        'marginRight': '12px'
    },
    'top': {
        'height': '46px',
        'justifyContent': 'center',}
}

# Top row style
top_row_style = {
    'backgroundColor': card_color,
    'color': 'white',
    # 'display': 'flex',
    'padding': '20px',
    # 'height': 'auto',
    # 'justifyContent': 'flex-start',
}

# Container Style
container_style = {
    'backgroundColor': background_color,
    'padding': '25px',
    'justifyContent': 'center',
    'fontFamily': 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial',
    'color': '#FFFFFF',
    'maxWidth': '1200px',
    'margin': '0 auto',
}

def create_stat_row(title: str, metrics: Dict[str, str], style, large_text_color) -> dbc.Col:
    """Creates a statistics row with consistent styling"""
    return dbc.Col(
        dbc.Card(
            style={**card_styles['stat_card'], **style},
            children=[
                html.H2(
                    title,
                    style={
                        'color': large_text_color,
                        'textAlign': 'center',
                        'marginBottom': '20px',
                        'fontSize': '1.8em',
                        'letterSpacing': '0.05em'
                    }
                ),
                dbc.Row([
                    dbc.Col([
                        html.H4(
                            key,
                            style={
                                'color': large_text_color,
                                'fontSize': '1.2em',
                                'marginBottom': '10px',
                                'letterSpacing': '0.02em'
                            }
                        ),
                        html.P(
                            value,
                            style={
                                'fontSize': '1.1em',
                                'letterSpacing': '0.02em',
                                'marginTop': '5px'
                            }
                        )
                    ]) for key, value in metrics.items()
                ])
            ]
        ),
        style={'marginRight': 'auto', 'marginLeft': 'auto'}
    )

def create_image_text_block(text, image, style=None):
    """Creates an image-text block with consistent styling"""
    return html.Div(
        style=style or {
            # 'display': 'flex',
            # 'alignItems': 'flex-start',
            'backgroundColor': card_color,
            'color': 'white',
            # 'padding': '15px 20px',
            # 'margin': '10px 0',
            # 'borderRadius': '6px',
            'fontSize': '1.1em',
            # 'letterSpacing': '0.02em'
        },
        children=[
            html.Img(
                src=f'assets/{image}',
                style=image_styles['bottom']
            ),
            html.Span(
                text,
                style={
                    'flexGrow': 1,
                    'paddingLeft': '5px'
                }
            )
        ]
    )