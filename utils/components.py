from dash import html
from utils.dash_utils import large_text_color, small_text_color

def create_metric_section(image, value, label, show_image=False):
    """Create a metric section with consistent styling"""
    children = []
    if show_image:
        children.append(html.Img(src=f'assets/{image}', style={'height': '40px', 'width': 'auto', 'marginBottom': '10px'}))
    
    children.extend([
        html.Div(value, style={
            'color': large_text_color,
            'fontSize': '24px',
            'margin': '10px 0',
            'textAlign': 'center',
            'wordWrap': 'break-word',
            'width': '100%'
        }),
        html.Div(label, style={
            'color': small_text_color,
            'textAlign': 'center',
            'width': '100%'
        })
    ])
    
    return html.Div(
        style={
            'display': 'flex',
            'flexDirection': 'column',
            'alignItems': 'center',
            'justifyContent': 'center',
            'flex': '1',
            'padding': '20px',
            'minWidth': '0'  # Allow flex items to shrink below content size
        },
        children=children
    )

def create_stat_section(stats_list):
    """Create a stats section with consistent styling"""
    return html.Div(
        style={
            'display': 'flex',
            'flexDirection': 'column',
            'justifyContent': 'center',
            'flex': '1',
            'padding': '20px'
        },
        children=[
            html.Div(
                style={'display': 'flex', 'justifyContent': 'space-between', 'marginBottom': '10px'},
                children=[
                    html.Span(text, style={'color': 'white'}),
                    html.Span(value, style={'color': large_text_color, 'marginLeft': '10px'})
                ]
            ) for text, value in stats_list
        ]
    ) 