from typing import Dict, List, Tuple
import pandas as pd
from dash import html
import dash_bootstrap_components as dbc
from .calculate import calculate_mining_effort, calculate_time_to_find_block

def create_stat_row(title: str, metrics: Dict[str, str], style, large_text_color) -> dbc.Col:
    return dbc.Col(
        dbc.Card(
            style=style,
            children=[
                html.H2(title, style={'color': large_text_color, 'textAlign': 'center'}),
                dbc.Row([
                    dbc.Col([
                        html.H4(key, style={'color': large_text_color}),
                        html.P(value)
                    ]) for key, value in metrics.items()
                ])
            ]
        ),
        style={'marginRight': 'auto', 'marginLeft': 'auto'}
    )

def calculate_pool_stats(sharkapi) -> Dict[str, str]:
    block_data = sharkapi.get_block_stats()
    block_df = pd.DataFrame(block_data)
    pool_data = sharkapi.get_pool_stats()
    
    try:
        recent_block = max(block_df['created'])
        pool_effort = calculate_mining_effort(
            pool_data['networkdifficulty'], 
            pool_data['networkhashrate'],
            pool_data['poolhashrate'], 
            recent_block
        )
    except Exception:
        pool_effort = 0

    pool_ttf = calculate_time_to_find_block(
        pool_data['networkdifficulty'], 
        pool_data['networkhashrate'], 
        pool_data['poolhashrate']
    )
    pool_hash = round(pool_data['poolhashrate'] / 1e9, 2)

    return {
        "Hashrate": f"{pool_hash} GH/s",
        "TTF": f"{pool_ttf} Days",
        "Effort": f"{pool_effort}%"
    }

def calculate_miner_stats(sharkapi, wallet: str, pool_data: Dict) -> Dict[str, str]:
    # Use sync version instead of async
    miner_data = sharkapi.sync_get_miner_stats(wallet)
    miner_hash = round(miner_data.current_hashrate / 1e6, 2)
    
    try:
        my_recent_block = miner_data.last_block_found['timestamp']
        miner_effort = calculate_mining_effort(
            pool_data['networkdifficulty'], 
            pool_data['networkhashrate'],
            miner_hash * 1e6, 
            my_recent_block
        )
    except Exception:
        miner_effort = 0

    miner_ttf = calculate_time_to_find_block(
        pool_data['networkdifficulty'], 
        pool_data['networkhashrate'], 
        miner_hash * 1e6
    )

    return {
        "Hashrate": f"{miner_hash} MH/s",
        "TTF": f"{miner_ttf} Days",
        "Effort": f"{miner_effort}%"
    }