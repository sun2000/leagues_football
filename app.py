# standard library
#https://github.com/plotly/dash/issues/844
import os

# dash libs
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import plotly.figure_factory as ff
import base64
import glob
import os

import plotly.graph_objs as go
import dash_table


import dash_bootstrap_components as dbc


# pydata stack
import pandas as pd
from sqlalchemy import create_engine


# set params
conn = create_engine(os.environ['DB_URI']) #'sqlite:///data/soccer-stats.db'


###########################
# Data Manipulation / Model
###########################

def fetch_data(q):
    result = pd.read_sql_query(
        sql=q,
        con=conn
    )
    return result


def get_divisions():
    '''Returns the list of divisions that are stored in the database'''

    division_query = '''SELECT DISTINCT division FROM results'''
    divisions = fetch_data(division_query)
    divisions = list(divisions['division'].sort_values(ascending=True))
    return divisions



def get_seasons(division):
    '''Returns the seasons of the datbase store'''

    # seasons_query =  f"SELECT DISTINCT season FROM results WHERE division='{division}'"
    seasons = fetch_data(f"SELECT DISTINCT season FROM results WHERE division='{division}'")
    seasons = list(seasons['season'].sort_values(ascending=False))
    return seasons


def get_teams(division, season):
    '''Returns all teams playing in the division in the season'''

    # teams_query = f"SELECT DISTINCT team FROM results WHERE division='{division}' AND season='{season}'"
    teams = fetch_data(f"SELECT DISTINCT team FROM results WHERE division='{division}' AND season='{season}'")
    teams = list(teams['team'].sort_values(ascending=True))
    return teams


def get_match_results(division, season, team):
    '''Returns match results for the selected prompts'''

    # results_query = f"SELECT date, team, opponent, goals, goals_opp, result, points FROM results WHERE division='{division}' AND season='{season}' AND team='{team}' ORDER BY date ASC"
    match_results = fetch_data(f"SELECT date, team, opponent, goals, goals_opp, result, points FROM results WHERE division='{division}' AND season='{season}' AND team='{team}' ORDER BY date ASC")
    return match_results


def get_match_results_division_season(division, season):
    '''Returns match results for the selected prompts'''

    # results_query = f"SELECT A.* , ROW_NUMBER() OVER (ORDER BY points DESC) Rank FROM (SELECT team, sum(goals) as goals, SUM(CASE WHEN result = 'W' THEN 1 Else 0 END) as win, SUM(CASE WHEN result = 'L' THEN 1 Else 0 END) as lose, SUM(CASE WHEN result = 'D' THEN 1 Else 0 END) as draw, sum(points) as points FROM results where division= '{division}' and season='{season}' GROUP BY  division, season, team ORDER BY points DESC) as A"
    match_results = fetch_data(f"""SELECT team, sum(goals) as goals, SUM(CASE WHEN result = 'W' THEN 1 Else 0 END) as win, SUM(CASE WHEN result = 'D' THEN 1 Else 0 END) as draw, SUM(CASE WHEN result = 'L' THEN 1 Else 0 END) as lose, sum(points) as points FROM results where division= '{division}' and season='{season}' GROUP BY  division, season, team ORDER BY points DESC,  win DESC, lose, draw DESC, goals DESC""")
    # SELECT A.* , ROW_NUMBER() OVER (ORDER BY points DESC) Rank FROM
    # match_results['rank']= (match_results.sort_values(by=['points', 'win', 'draw', 'lose'], ascending = (False, False, False, True))['points']).rank(method='max')
    # match_results.sort_values(by=['points'], inplace=True, ascending=False)
    # match_results['rank']= (match_results['points']).rank(method='min')
    match_results['rank'] = match_results.index + 1
    # df.groupby('Auction_ID')['Bid_Price'].rank(ascending=False)
    # match_results['rank']=match_results.groupby(['division', 'season'])['points'].rank(ascending=False)
    # match_results=match_results.drop(['division', 'season'], axis=1)
    # match_results.sort_values(by=['rank'], inplace=True, ascending=False)
        # f"""SELECT A.* , ROW_NUMBER() OVER (ORDER BY points DESC) Rank
        # FROM (
        #     SELECT team,
        #         sum(goals) as goals,
        #         SUM(CASE WHEN result = 'W' THEN 1 Else 0 END) as win,
        #         SUM(CASE WHEN result = 'L' THEN 1 Else 0 END) as lose,
        #         SUM(CASE WHEN result = 'D' THEN 1 Else 0 END) as draw,
        #         sum(points) as points
        #     FROM results where division= '{division}'
        #     and season='{season}'
        #     GROUP BY  division, season, team ORDER BY points DESC
        #     ) as A
        # """
        # )
    return match_results



def calculate_season_summary(results):
    record = results.groupby(by=['result'])['team'].count()
    summary = pd.DataFrame(
        data={
            'Matchs Winner': record['W'],
            'Matchs Loser': record['L'],
            'Matchs Drawer': record['D'],
            'Total Points': results['points'].sum()
        },
        columns=['Matchs Winner', 'Matchs Drawer', 'Matchs Loser', 'Total Points'],
        index=results['team'].unique()
    )
    return summary


def draw_season_points_graph(results, division, season, team):

    dates = results['date']
    points = results['points'].cumsum()

    figure = go.Figure(
        data=[
            go.Scatter(x=dates, y=points, mode='lines+markers', showlegend=False)
        ],
        layout=go.Layout(
            # title=html.Span('First Part lknqkcnqcknq'),
            title='<span style="font-size: 12px;">Points Accumulation for team {}, season {}, division {}</span>'.format(team , season, division),
            showlegend=True
        )
    )

    return figure


def draw_barchart_season_division_graph(results, division, season):
    # sort Rank - descending order
    results.sort_values(by=['rank'], inplace=True, ascending=False)
    teams = results['team']
    points = results['points']

    data=[
        go.Bar(x=points, y=teams, orientation='h', textposition='auto')
    ]
    layout=go.Layout(
        title=('<span style="font-size: 12px;">Teams ranking for {} division and {} season</span>'.format(division, season)),
        showlegend=False,
        margin=dict(l=100, r=20, t=70, b=70),
        xaxis={'categoryorder':'total descending'}
    )
    figure = go.Figure(data=data, layout = layout)

    return figure



#########################
# Dashboard Layout / View
#########################

def generate_table(dataframe, max_rows=10):
    '''Given dataframe, return template generated using Dash components
    '''
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )

# def generate_table(df):
    # return html.Div(
    #     [dash_table.DataTable(
    #         columns=[{"name": i, "id": i} for i in df.columns],
    #         data=df.to_dict('records'),
    #         pagination_mode='fe',
    #         pagination_settings={
    #             'displayed_pages': 1,
    #             'current_page': 0,
    #             'page_size': 20,
    #         },
    #     )]
    # )




def onLoad_division_options():
    '''Actions to perform upon initial page load'''

    division_options = (
        [{'label': division, 'value': division}
         for division in get_divisions()]
    )
    return division_options


# # Set up Dashboard and create layout
# external_stylesheets=[
#     'https://codepen.io/chriddyp/pen/bWLwgP.css'
# ]
# app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
# app = dash.Dash(csrf_protect=False)

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
app.config['suppress_callback_exceptions']=True

# app.css.config.serve_locally = False

# app.css.append_css({
#     # "external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"
#     "external_url": "/static/Bootstrap.css"
# })

#fix issue heroku : Failed to find application: 'app'
server = app.server


image_filename = 'assets/Bundesliga1.png' # replace with your own image
encoded_image = base64.b64encode(open(image_filename, 'rb').read())

#
# colors = {
#     'background': '#111111',
#     'text': '#7FDBFF'
# }

# style={'backgroundColor': colors['background']}, children=

initial_division_value = get_divisions()[0]
print("initial_division_value: {}".format(initial_division_value))
initial_season_value = get_seasons(initial_division_value)[0]
print("initial_season_value: {}".format(initial_season_value))
initial_team = get_teams(initial_division_value, initial_season_value)[0]
print("initial_team: {}".format(initial_team))



# https://community.plotly.com/t/is-there-a-way-to-synchronize-dropdowns-across-tabs/18244/2
tab1_layout = [
        dbc.Row([
            dbc.Col(
                html.H1("Soccer Results Viewer"),
                width={"size": 11,  "offset": 0} # lg=3, md=6, xs=12
            ),
            dbc.Col(
                dbc.Card(
                    dbc.CardImg(
                        id="logo-id-tab1",
                        style={
                            'height': '100px',
                            'width': '80px',
                            # 'float': 'right',
                            'position': 'relative',
                            'padding-top': 1,
                            'padding-right': 1,
                            # "background": "black",
                            # "border-color": "#FF0000",
                            # "border-width": "5%",
                            "border":"1px double black"
                        }
                    )
                ),
                width={"size": 1, "offset": 0}
            )
        ]),
        html.Br(),
        #
        dbc.Row([
            dbc.Col(
                # Select Division Dropdown
                html.Label(
                    [
                        "Select Division",
                        dcc.Dropdown(
                            id='division-selector-tab1',
                            value=initial_division_value,
                            options=onLoad_division_options(),
                            style={
                                # 'height': '5px',
                                'width': '150%',
                                # 'font-size': "50%",
                                # 'min-height': '3px',
                            },
                        )
                    ]
                ),
                # width={"size": 4} #, "lg": 4, "md": 8, "sm": 10,  "xs": 12} ##width="auto" , "offset": 1
            ),
            dbc.Col(
                # Select Division Dropdown
                html.Label(
                    [
                        "Select Season",
                        dcc.Dropdown(
                            id='season-selector-tab1',
                            value=initial_season_value,
                            style={
                            #     'height': '2px',
                                'width': '150%',
                            #     'font-size': "50%",
                            #     'min-height': '1px',
                            },
                        )
                    ]
                ),
                # width={"size": 4} #, "lg": 2, "md": 8, "sm": 10,  "xs": 12}
                #width="auto" #{"lg": 4, "md": 8, "sm": 10, "xs": 12 } # "size": 4
            )
            ], justify="left", no_gutters = False), #j,
            # html.H3("Soccer Results Viewer"),
            html.Br(),
            html.Br(),
            dbc.Row([
                dbc.Col(
                    # Select Division Dropdown
                    html.Table(id='match-results'),
                    # width={"size": 5, "lg": 4, "md": 8, "sm": 10,  "xs": 12, "offset": 1}
                ),
                dbc.Col(
                    # Select Division Dropdown
                    # barchart by division
                    dcc.Graph(id='bar-chart-graph'),
                    # width={"size": 5,  "lg": 4, "md": 8, "sm": 10,  "xs": 12,  "offset": 0}
                )
            ])
]


tab2_layout =  [
        dbc.Row([
            dbc.Col(
                html.H1("Soccer Results Viewer"),
                width={"size": 11,  "offset": 0} # lg=3, md=6, xs=12
            ),
            dbc.Col(
                dbc.Card(
                    dbc.CardImg(
                        id="logo-id-tab2",
                        style={
                                'height': '100px',
                                'width': '80px',
                                # 'float': 'right',
                                'position': 'relative',
                                'padding-top': 1,
                                'padding-right': 1,
                                # "background": "black",
                                # "border-color": "#FF0000",
                                # "border-width": "5%",
                                "border":"1px double black"
                        }
                    )
                ),
                width={"size": 1, "offset": 0, "padding-right": "5%"}
            )
        ]),
        html.Br(),
        #
        dbc.Row([
            dbc.Col(
                # Select Division Dropdown
                html.Label(
                    [
                        "Select Division",
                        dcc.Dropdown(
                            id='division-selector-tab2',
                            options=onLoad_division_options(),
                            value=initial_division_value,
                            style={
                                # 'height': '5px',
                                'width': '150%',
                                # 'font-size': "50%",
                                # 'min-height': '3px',
                            },
                        )
                    ]
                ),
                # width={"size": 4} #, "lg": 4, "md": 8, "sm": 10,  "xs": 12} ##width="auto" , "offset": 1
            ),
            dbc.Col(
                # Select Division Dropdown
                html.Label(
                    [
                        "Select Season",
                        dcc.Dropdown(
                            id='season-selector-tab2',
                            value=initial_season_value,
                            style={
                            #     'height': '2px',
                                'width': '150%',
                            #     'font-size': "50%",
                            #     'min-height': '1px',
                            },
                        )
                    ]
                )
                # ,  width={"size": 4} #, "lg": 2, "md": 8, "sm": 10,  "xs": 12}
                #width="auto" #{"lg": 4, "md": 8, "sm": 10, "xs": 12 } # "size": 4
            ),
            dbc.Col(
                # Select Division Dropdown
                html.Label(
                    [
                        "Select Team to view details",
                        dcc.Dropdown(
                            id='team-selector-tab2',
                            value=initial_team,
                            # style={
                            # #     'height': '2px',
                            #     'width': '150%',
                            # #     'font-size': "50%",
                            # #     'min-height': '1px',
                            # },
                        )

                    ]
                ),
                # width={"size": 4} #, "lg": 4, "md": 8, "sm": 10,  "xs": 12}
                #width="auto" #width={"lg": 4, "md": 8, "sm": 10, "xs": 12, "offset": 1}
            ),
        ], justify="left", no_gutters = False),
        dbc.Row([
            dbc.Col(
                dcc.Graph(id='season-summary'),
                # width={"size": 12} # "offset": -1
            ),
            dbc.Col(
                # summary table
                # graph
                dcc.Graph(id='season-graph'),
                # width={"size": 12}
            )
        ]),
]


app.layout = html.Div([
    dcc.Store(id='division-selector-cache', storage_type='session', data=initial_division_value),
    dcc.Store(id='season-selector-cache', storage_type='session', data=initial_season_value),
    html.Div([
        dcc.Tabs(
            id='tabs',
            children=[
                dcc.Tab(
                    label='Leagues Results',
                    value=1,
                    children=tab1_layout
                ),
                dcc.Tab(
                    label='Detail for Selectionned Team',
                    value=2,
                    children=tab2_layout
                ),
            ]),
    ]),
    html.Div(id='tab-output')
], style={ "padding-left": "5%", "padding-right": "5%"})



#############################################
# Interaction Between Components / Controller
#############################################

# callback portion for synchronizing dropdown across tabs.
@app.callback(
    Output('division-selector-cache', 'data'),
    [Input('division-selector-tab1', 'value'),
     Input('division-selector-tab2', 'value')],
     [State('tabs', 'value')]
)
def store_dropdown_cache(
    tab_1_division_selector,
    tab_2_division_selector,
    tab
):
    print("tab_1_division_selector {}".format(tab_1_division_selector))
    print("tab_2_division_selector {}".format(tab_2_division_selector))
    if tab == 1:
        print("tab_1_division_selector {}".format(tab_1_division_selector))
        return tab_1_division_selector #[tab_1_division_selector, tab_1_season_selector]
    elif tab == 2:
        print("tab_2_division_selector {}".format(tab_2_division_selector))
        return tab_2_division_selector #[tab_2_division_selector, tab_2_season_selector]


# Note that using drodowns-cache as an input to change the
# dropdown value breaks the layout. I feel this has something
# to do with circular reference, but using the state w/tab
# value as the input callback trigger works!
@app.callback(
    Output('division-selector-tab1', 'value'),
    [Input('tabs', 'value')],
    [State('division-selector-cache', 'data')]
)
def synchronize_dropdowns(_, cache):
    print("cache1: {}".format(cache))
    print("cache1_: {}".format(_))
    return cache

@app.callback(
    Output('division-selector-tab2', 'value'),
    [Input('tabs', 'value')],
    [State('division-selector-cache', 'data')]
)
def synchronize_dropdowns(_, cache):
    print("cache2: {}".format(cache))
    print("cache2_: {}".format(_))
    return cache


image_directory = 'assets/'
list_of_images = [os.path.basename(x) for x in glob.glob('{}*.png'.format(image_directory))]
print("list_of_images: {}".format(list_of_images))


@app.callback(
    Output('logo-id-tab1', 'src'),
    [Input('division-selector-tab1', 'value')]
)
def update_image_src(division):
    image_name = '{}.png'.format(division)
    print("image_name: {}".format(image_name))

    if image_name not in list_of_images:
        raise Exception('"{}" is excluded from the allowed static images'.format(image_directory))
    image_filename = image_directory + str(division) + ".png"
    print("image_name: {}".format(image_name))
    encoded_image =  base64.b64encode(open(image_filename, 'rb').read())
    return('data:image/png;base64,{}'.format(encoded_image.decode()))



@app.callback(
    Output('logo-id-tab2', 'src'),
    [Input('division-selector-tab2', 'value')]
)
def update_image_src(division):
    image_name = '{}.png'.format(division)
    print("image_name: {}".format(image_name))

    # if image_name not in list_of_images:
    #     raise Exception('"{}" is excluded from the allowed static images'.format(image_directory))
    image_filename = image_directory + str(division) + ".png"
    print("image_name: {}".format(image_name))
    encoded_image =  base64.b64encode(open(image_filename, 'rb').read())
    return('data:image/png;base64,{}'.format(encoded_image.decode()))




# Load Seasons in Dropdown
@app.callback(
    Output(component_id='season-selector-tab1', component_property='options'),
    [
        Input(component_id='division-selector-tab1', component_property='value')
    ]
)
def populate_season_selector(division):
    seasons = get_seasons(division)
    # print("seasons: {}".format(seasons))
    return [
        {'label': season, 'value': season}
        for season in seasons
    ]


# Load Seasons in Dropdown
@app.callback(
    Output(component_id='season-selector-tab2', component_property='options'),
    [
        Input(component_id='division-selector-tab2', component_property='value')
    ]
)
def populate_season_selector(division):
    seasons = get_seasons(division)
    # print("seasons: {}".format(seasons))
    return [
        {'label': season, 'value': season}
        for season in seasons
    ]


# # season-selector-tab tab1
# @app.callback(
#     Output(component_id='season-selector-tab1', component_property='value'),
#     [Input(component_id='season-selector-tab1', component_property='options')]
# )
# def set_season_selector(available_options):
#     print("season-selector-tab1 options: {}".format(available_options))
#     return available_options[0]['value']
#
#
#
# @app.callback(
#     Output(component_id='season-selector-tab2', component_property='value'),
#     [Input(component_id='season-selector-tab2', component_property='options')]
# )
# def set_season_selector(available_options):
#     print("season-selector-tab2 options: {}".format(available_options))
#     return available_options[0]['value']

# callback portion for synchronizing dropdown across tabs.
@app.callback(
    Output('season-selector-cache', 'data'),
    [Input('season-selector-tab1', 'value'),
     Input('season-selector-tab2', 'value')],
     [State('tabs', 'value')]
)
def store_dropdown_cache(
    tab_1_season_selector,
    tab_2_season_selector,
    tab
):
    if tab == 1:
        return tab_1_season_selector #[tab_1_division_selector, tab_1_season_selector]
    elif tab == 2:
        return tab_2_season_selector #[tab_2_division_selector, tab_2_season_selector]


# Note that using drodowns-cache as an input to change the
# dropdown value breaks the layout. I feel this has something
# to do with circular reference, but using the state w/tab
# value as the input callback trigger works!

@app.callback(
    Output('season-selector-tab1', 'value'),
    [Input('tabs', 'value')],
    [State('season-selector-cache', 'data')]
)
def synchronize_dropdowns(_, cache):
    return cache

@app.callback(
    Output('season-selector-tab2', 'value'),
    [Input('tabs', 'value')],
    [State('season-selector-cache', 'data')]
)
def synchronize_dropdowns(_, cache):
    return cache


# Load Teams into dropdown
@app.callback(
    Output(component_id='team-selector-tab2', component_property='options'),
    [
        Input(component_id='division-selector-tab2', component_property='value'),
        Input(component_id='season-selector-tab2', component_property='value')
    ]
)
def populate_team_selector(division, season):
    print("division: ".format(division))
    print("season: ".format(season))
    teams = get_teams(division, season)
    print("teams: {}".format(teams))
    return [
        {'label': team, 'value': team}
        for team in teams
    ]

# update team
@app.callback(
    Output(component_id='team-selector-tab2', component_property='value'),
    [
        Input(component_id='team-selector-tab2', component_property='options'),
    ]
)
def set_season_selector(available_options):
    print("available_options: {}".format(available_options))
    return available_options[0]['value']


# Load Match results
@app.callback(
    Output(component_id='match-results', component_property='children'),
    [
        Input(component_id='division-selector-tab1', component_property='value'),
        Input(component_id='season-selector-tab1', component_property='value'),
        # Input(component_id='team-selector', component_property='value')
    ]
)
def load_match_results(division, season):
    results = get_match_results_division_season(division, season)
    return generate_table(results, max_rows=results.shape[0])


# Update Season Summary Table
@app.callback(
    Output(component_id='season-summary', component_property='figure'),
    [
        Input(component_id='division-selector-tab2', component_property='value'),
        Input(component_id='season-selector-tab2', component_property='value'),
        Input(component_id='team-selector-tab2', component_property='value')
    ]
)
def load_season_summary(division, season, team):
    results = get_match_results(division, season, team)

    table = []#dash.no_update
    if len(results) > 0:
        summary = calculate_season_summary(results)
        table = ff.create_table(summary)
        # Update the margins to add a title and see graph x-labels.
        table.layout.margin.update({'t':75, 'l':50})
        table.layout.update({'title': '<span style="font-size: 12px;"> Summary for team {}, season {}, division {}</span>'.format(team , season, division)})

    return table


# Update Season Point Graph
@app.callback(
    Output(component_id='season-graph', component_property='figure'),
    [
        Input(component_id='division-selector-tab2', component_property='value'),
        Input(component_id='season-selector-tab2', component_property='value'),
        Input(component_id='team-selector-tab2', component_property='value')
    ]
)
def load_season_points_graph(division, season, team):
    results = get_match_results(division, season, team)

    figure = []#dash.no_update
    if len(results) > 0:
        figure = draw_season_points_graph(results, division, season, team)

    return figure


# Update Season Bar Chart Graph
@app.callback(
    Output(component_id='bar-chart-graph', component_property='figure'),
    [
        Input(component_id='division-selector-tab1', component_property='value'),
        Input(component_id='season-selector-tab1', component_property='value')
    ]
)
def load_season_division_points_graph(division, season):
    results = get_match_results_division_season(division, season)

    figure = []#dash.no_update
    if len(results) > 0:
        figure = draw_barchart_season_division_graph(results, division, season)

    return figure


# start Flask server
if __name__ == '__main__':
    app.run_server(
        debug=True,
        threaded=True,
    )
