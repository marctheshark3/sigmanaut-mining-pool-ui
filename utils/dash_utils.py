from dash import html, dash_table, dcc
import dash_bootstrap_components as dbc
from typing import Dict
from datetime import datetime

# Colors
card_color = '#27374D'
background_color = '#526D82'
large_text_color = '#9DB2BF'
small_text_color = '#DDE6ED'

# Card Styles
top_card_style = {
    'backgroundColor': card_color,
    'color': small_text_color,
    'height': '225px',  # Fixed height for all cards
    'padding': '30px',
    'borderRadius': '8px',
    'textAlign': 'center',
    'display': 'flex',
    'flexDirection': 'column',
    'alignItems': 'center',
    'justifyContent': 'center',
    'margin': '0',  # Remove margin since we're using column padding
    'border': 'none'
}

top_image_style = {
    'width': '60px',
    'height': '60px',
    'marginBottom': '15px',
    'filter': 'brightness(0) invert(1)'  # Make icons white
}

bottom_row_style = {
    'backgroundColor': card_color,
    'color': small_text_color,
    'padding': '20px',
    'borderRadius': '8px',
    'height': '100%',
    'display': 'flex',
    'flexDirection': 'column',
    'justifyContent': 'space-between'
}

container_style = {
    'backgroundColor': background_color,
    'padding': '25px',
    'maxWidth': '1200px',
    'margin': '0 auto',
    'fontFamily': 'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial',
    'color': '#FFFFFF'
}

# Table Styles
table_style = {
    'backgroundColor': card_color,
    'color': large_text_color,
    'fontWeight': 'bold',
    'textAlign': 'center',
    'border': '1px solid black',
    'padding': '15px'
}

# First row text styles
first_row_styles = {
    'value': {
        'color': large_text_color,
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

# Row Styles
top_row_style = {
    'backgroundColor': card_color,
    'color': 'white',
    'display': 'flex',
    'padding': '20px',
    'height': 'auto',
    'justifyContent': 'flex-start',
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

def get_days_ago(timestamp: str) -> str:
    """Convert timestamp to 'X days ago' format"""
    if not timestamp:
        return "Never"
    
    try:
        # Parse the timestamp
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        now = datetime.now(dt.tzinfo)
        
        # Calculate the difference
        diff = now - dt
        days = diff.days
        
        if days == 0:
            hours = diff.seconds // 3600
            if hours == 0:
                return "Today"
            return f"{hours} hours ago"
        elif days == 1:
            return "Yesterday"
        else:
            return f"{days} days ago"
    except Exception:
        return "Unknown"