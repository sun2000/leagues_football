# standard library
import os

# dash libs
import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import plotly.figure_factory as ff
import base64
import glob
import os

import plotly.graph_objs as go


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
    match_results = fetch_data(f"""SELECT team, sum(goals) as goals, SUM(CASE WHEN result = 'W' THEN 1 Else 0 END) as win, SUM(CASE WHEN result = 'D' THEN 1 Else 0 END) as draw, SUM(CASE WHEN result = 'L' THEN 1 Else 0 END) as lose, sum(points) as points FROM results where division= '{division}' and season='{season}' GROUP BY  division, season, team ORDER BY points DESC,  win DESC, lose, draw DESC""")
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
        index=results['team'].unique(),
    )
    return summary


def draw_season_points_graph(results, division, season, team):

    dates = results['date']
    points = results['points'].cumsum()

    figure = go.Figure(
        data=[
            go.Scatter(x=dates, y=points, mode='lines+markers')
        ],
        layout=go.Layout(
            title='Points Accumulation for team {}, season {}, division {}'.format(team , season, division),
            showlegend=False
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
app = dash.Dash(csrf_protect=False)

# app.css.config.serve_locally = False

app.css.append_css({
    "external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"
})
# app.css.append_css({
#     "external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"
#     # "external_url": "/static/Bootstrap.css"
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
initial_season_value = get_seasons(initial_division_value)[0]

app.layout = html.Div(
    [
        html.Div(
            [
                # Page Header
                html.Div(
                    [
                        html.H1('Soccer Results Viewer', className="nine columns"),
                        html.Img(id="image",

                            # # src="/assets/bundesliga.png",
                            # src='data:image/png;base64,{}'.format(encoded_image.decode()),
                            # className='three columns',
                            style={
                                'height': '7%',
                                'width': '7%',
                                'float': 'right',
                                'position': 'relative',
                                'padding-top': 0,
                                'padding-right': 0
                            },
                        ),
                    ]
                )
            ], className="row"
        ),
        # Dropdown Grid
        html.Div(
            [
                html.Div(
                    [
                        html.P('Select Division'),
                        # Select Division Dropdown
                        dcc.Dropdown(
                            id='division-selector',
                            options=onLoad_division_options(),
                            value=initial_division_value
                        )
                    ],
                    className='four columns',
                    style={'margin-top': '10'}
                ),

                # Select Season Dropdown
                html.Div(
                    [
                        html.P('Select Season'),
                        html.Div(
                            dcc.Dropdown(
                                id='season-selector',
                                value=initial_season_value
                            )
                        )
                    ],
                    className='four columns',
                    style={'margin-top': '10'}
                ),
                # Select Team Dropdown
                html.Div(
                    [
                        html.Div('Select Team to view details'),
                        html.Div(
                            dcc.Dropdown(
                                id='team-selector'
                            )
                        )
                    ],
                    className='four columns',
                    style={'margin-top': '10'}
                )
            ], className="row"
        ),
        # Match Results Grid
        html.Div(
            [
                # Match Results Table
                html.Div(
                    [
                        html.Table(id='match-results'),
                    ],
                    className='six columns',
                    style={'margin-top': '10'}
                ),
                # Match Results Table
                html.Div(
                    [
                        # barchart by division
                        dcc.Graph(id='bar-chart-graph')
                    ],
                    className='six columns',
                    style={'margin-top': '10'}
                )
            ], className="row"
        ),
        html.Div(
            [
                # Season Summary Table and Graph
                html.Div(
                    [
                    # summary table
                        dcc.Graph(id='season-summary'),

                        # graph
                        dcc.Graph(id='season-graph')
                        # style={},
                    ],
                )
            ],
        )
    ], className='ten columns offset-by-one'
)


#############################################
# Interaction Between Components / Controller
#############################################
image_directory = 'assets/'
list_of_images = [os.path.basename(x) for x in glob.glob('{}*.png'.format(image_directory))]
print("list_of_images: {}".format(list_of_images))

@app.callback(
    dash.dependencies.Output('image', 'src'),
    [dash.dependencies.Input('division-selector', 'value')])
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
    Output(component_id='season-selector', component_property='options'),
    [
        Input(component_id='division-selector', component_property='value')
    ]
)
def populate_season_selector(division):
    seasons = get_seasons(division)
    # print("seasons: {}".format(seasons))
    return [
        {'label': season, 'value': season}
        for season in seasons
    ]


# Load Teams into dropdown
@app.callback(
    Output(component_id='team-selector', component_property='options'),
    [
        Input(component_id='division-selector', component_property='value'),
        Input(component_id='season-selector', component_property='value')
    ]
)
def populate_team_selector(division, season):
    teams = get_teams(division, season)
    return [
        {'label': team, 'value': team}
        for team in teams
    ]


# Load Match results
@app.callback(
    Output(component_id='match-results', component_property='children'),
    [
        Input(component_id='division-selector', component_property='value'),
        Input(component_id='season-selector', component_property='value'),
        # Input(component_id='team-selector', component_property='value')
    ]
)
def load_match_results(division, season):
    results = get_match_results_division_season(division, season)
    return generate_table(results, max_rows=10)


# Update Season Summary Table
@app.callback(
    Output(component_id='season-summary', component_property='figure'),
    [
        Input(component_id='division-selector', component_property='value'),
        Input(component_id='season-selector', component_property='value'),
        Input(component_id='team-selector', component_property='value')
    ]
)
def load_season_summary(division, season, team):
    results = get_match_results(division, season, team)

    table = []
    if len(results) > 0:
        summary = calculate_season_summary(results)
        table = ff.create_table(summary)
        # Update the margins to add a title and see graph x-labels.
        table.layout.margin.update({'t':75, 'l':50})
        table.layout.update({'title': 'Summary for team {}, season {}, division {}'.format(team , season, division)})

    return table


# Update Season Point Graph
@app.callback(
    Output(component_id='season-graph', component_property='figure'),
    [
        Input(component_id='division-selector', component_property='value'),
        Input(component_id='season-selector', component_property='value'),
        Input(component_id='team-selector', component_property='value')
    ]
)
def load_season_points_graph(division, season, team):
    results = get_match_results(division, season, team)

    figure = []
    if len(results) > 0:
        figure = draw_season_points_graph(results, division, season, team)

    return figure


# Update Season Bar Chart Graph
@app.callback(
    Output(component_id='bar-chart-graph', component_property='figure'),
    [
        Input(component_id='division-selector', component_property='value'),
        Input(component_id='season-selector', component_property='value')
    ]
)
def load_season_division_points_graph(division, season):
    results = get_match_results_division_season(division, season)

    figure = []
    if len(results) > 0:
        figure = draw_barchart_season_division_graph(results, division, season)

    return figure



# start Flask server
if __name__ == '__main__':
    app.run_server(
        debug=True,
        threaded=True,
    )
