import sys
from datetime import date, datetime

import dash
import requests
import pandas as pd
import json
import numpy as np
import os
import plotly.express as px
from dash import html
from dash import dcc
from dash.dependencies import Output, Input
import dash_bootstrap_components as dbc

request_url = "https://www.nationallottery.co.za/index.php?task=results.redirectPageURL&amp;Itemid=265&amp;option=com_weaver&amp;controller=lotto-history"
update_request_url = "https://www.nationallottery.co.za/index.php?task=results.getViewAllURL&amp;Itemid=265&amp;option=com_weaver&amp;controller=lotto-history"
START_INDEX = 1500
END_INDEX = 2188
COLUMNS = ['drawNumber', 'drawDate', 'nextDrawDate', 'ball1', 'ball2', 'ball3', 'ball4', 'ball5', 'ball6', 'bonusBall',
           'div1Winners', 'div1Payout', 'div2Winners', 'div2Payout', 'div3Winners', 'div3Payout', 'div4Winners',
           'div4Payout', 'div5Winners', 'div5Payout', 'div6Winners', 'div6Payout', 'div7Winners', 'div7Payout',
           'div8Winners', 'div8Payout', 'rolloverAmount', 'rolloverNumber', 'totalPrizePool', 'totalSales',
           'estimatedJackpot', 'guaranteedJackpot', 'drawMachine', 'ballSet', 'status', 'ecwinners', 'mpwinners',
           'ncwinners', 'gpwinners', 'wcwinners', 'fswinners', 'kznwinners', 'nwwinners', 'winners', 'millionairs',
           'lpwinners']
DATAFRAME = None
START_DATE = "2015-08-01"
END_DATE = "2020-08-01"

def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd="\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()


def lotto_ball(number, colour):
    '''
    Creates an HTML element in the shape of a lotto ball.
    :param number: Number to be displayed on the ball.
    :param colour: Colour of the ball.
    :return: HTML element in the shape of the ball in the colour specified and with the specified number.
    '''
    return html.Div([html.Div([html.H1(f"{number}")], style={"line-height": "15px", "vertical-align": "middle",
                                                             "border-radius": "50%", "text-align": "center",
                                                             "background": "radial-gradient(circle at 25px 25px, #ffffff, #adadad)",
                                                             "width": "50px", "height": "50px",
                                                             "position": "absolute", "top": "50%",
                                                             "margin-top": "-25px"})], style={
        "border-radius": "50%",
        "height": "100px",
        "width": "100px",
        "margin-right": "15px",
        "text-align": "center",
        "vertical-align": "middle",
        "line-height": "100px",
        "display": "flex",
        "justify-content": "center",
        "position": "relative",
        "background": f"radial-gradient(circle at 50px 50px, {colour}, #5e5e5e 90%)"})


def get_ball_colour(number):
    '''
    Returns a colour for a given number.
    :param number: A number for the ball colour.
    :return: A string for the colour.
    '''
    if 1 <= number <= 13:
        return "red"
    elif 14 <= number <= 27:
        return "yellow"
    elif 28 <= number <= 38:
        return "green"
    else:
        return "Aqua"


def create_filtered_series(filtered_df: pd.DataFrame):
    '''
    Counts the number of occurrence of each lotto number.
    :param filtered_df: A dataframe filtered on dates.
    :return: A series containing the number of occurrence of each lotto number.
    '''
    filtered_series = pd.Series([0 for i in range(53)])
    ball_1_values = filtered_df['ball1'].value_counts()
    ball_2_values = filtered_df['ball2'].value_counts()
    ball_3_values = filtered_df['ball3'].value_counts()
    ball_4_values = filtered_df['ball4'].value_counts()
    ball_5_values = filtered_df['ball5'].value_counts()
    ball_6_values = filtered_df['ball6'].value_counts()
    bonus_ball_values = filtered_df['bonusBall'].value_counts()
    for k in ball_1_values.keys():
        filtered_series[k] += ball_1_values[k]
    for k in ball_2_values.keys():
        filtered_series[k] += ball_2_values[k]
    for k in ball_3_values.keys():
        filtered_series[k] += ball_3_values[k]
    for k in ball_4_values.keys():
        filtered_series[k] += ball_4_values[k]
    for k in ball_5_values.keys():
        filtered_series[k] += ball_5_values[k]
    for k in ball_6_values.keys():
        filtered_series[k] += ball_6_values[k]
    for k in bonus_ball_values.keys():
        filtered_series[k] += bonus_ball_values[k]
    return filtered_series


def get_ball_frequency(start_date, end_date):
    '''
    Filters a dataframe on the dates specified and returns the frequency of each lotto ball in the filtered dataframe.
    :param start_date: The start date of the filter
    :param end_date: The end date of the filter
    :return: A dataframe containing the frequency of each lotto ball
    '''
    filtered_df = DATAFRAME[(DATAFRAME['drawDate'] >= start_date) & (DATAFRAME['drawDate'] <= end_date)]
    ball_frequency = create_filtered_series(filtered_df)
    ball_frequency_df = ball_frequency.to_frame("Ball Frequency").fillna(0)
    ball_frequency_df.reset_index(level=0, inplace=True)
    ball_frequency_df.rename(columns={"index": "Ball Number"}, inplace=True)
    return ball_frequency_df


def get_last_draw():
    '''
    Get the information for the last lotto draw.
    :return: The last lotto draw.
    '''
    last_row = DATAFRAME.iloc[-1]
    return [last_row.iloc[i] for i in range(4, 10)]


def add_lottto_data(df, draw_index):
    '''
    Adds the next lotto draw data based on the draw index.
    :param df: The dataframe that should be updated.
    :param draw_index: The index of the lotto draw.
    '''
    printProgressBar(draw_index - START_INDEX, END_INDEX - START_INDEX, prefix=f"Collecting draw #{draw_index}")
    data = {
        "gameName": "LOTTO",
        "drawNumber": f"{draw_index}",
        "isAjax": "true"
    }
    result = requests.post(request_url, data=data)
    http_dict = json.loads(result.content)
    temp_df = pd.DataFrame(np.array(list(http_dict['data']['drawDetails'].values())).reshape((1, 46)),
                           columns=COLUMNS, index=[draw_index])
    df = df.append(temp_df)


def create_dashboard(app):
    '''
    Creates a dashboard of the lotto data.
    :param app: The dash applocation.
    '''
    app.layout = html.Div([
        dbc.NavbarSimple(
            brand="Lotto Dashboard",
            brand_href="#",
            color="primary",
            dark=True,
        ),
        dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.H4("Last Draw", className="card-title"),
                        # lotto_ball(i, get_ball_colour(i)) for i in [3, 8, 14, 19, 27, 31, 37, 49, 51]
                        dbc.Row([lotto_ball(i, get_ball_colour(i)) for i in get_last_draw()], id="last_draw")
                    ], className="offset-sm-1"
                ),
            ],
        ),
        dbc.Card([
            dbc.CardBody([
                html.H4("Ball Frequency", className="card-title"),
                dbc.Label("Select Date Range:", style={"padding-right": "20px"}),
                dcc.DatePickerRange(
                    id='my-date-picker-range',
                    min_date_allowed=date(1995, 8, 5),
                    max_date_allowed=date(2021, 12, 30),
                    initial_visible_month=date(2015, 1, 1),
                    start_date_placeholder_text=START_DATE,
                    end_date_placeholder_text=END_DATE,
                    end_date=date(2017, 8, 25)
                ),
                dcc.Graph(id='lotto_graph'),
                html.H4("Most frequent balls in given period", className="card-title"),
                html.H5("Most frequent balls in given period"),
                dbc.Row(id="most_frequent_id"),
                html.H5("2nd Most frequent balls in given period"),
                dbc.Row(id="2_frequent_id"),
                html.H5("3rd Most frequent balls in given period"),
                dbc.Row(id="3_frequent_id")
            ], className="offset-sm-1")
        ]),
    ])

    @app.callback(Output(component_id="lotto_graph", component_property='figure'),
                  Output(component_id="most_frequent_id", component_property='children'),
                  Output(component_id="2_frequent_id", component_property='children'),
                  Output(component_id="3_frequent_id", component_property='children'),
                  Input('my-date-picker-range', 'start_date'),
                  Input('my-date-picker-range', 'end_date'))
    def handler(start_date, end_date):
        if start_date == None:
            start_date = START_DATE
        if end_date == None:
            end_date = END_DATE
        filtered_df = get_ball_frequency(datetime.strptime(start_date, "%Y-%m-%d"),
                                         datetime.strptime(end_date, "%Y-%m-%d"))
        most_frequent_numbers = filtered_df.sort_values(by='Ball Frequency', ascending=False)['Ball Number'].values[
                                :18]
        return px.bar(data_frame=filtered_df, x="Ball Number",
                      y="Ball Frequency"), [lotto_ball(i, get_ball_colour(i)) for i in most_frequent_numbers[:6]], \
               [lotto_ball(i, get_ball_colour(i)) for i in most_frequent_numbers[6:12]], \
               [lotto_ball(i, get_ball_colour(i)) for i in most_frequent_numbers[12:18]]
        dataframe.sort_values(by='Ball Frequency', ascending=False)['Ball Number'].values[:6]
        return {}


if __name__ == "__main__":
    if not os.path.isfile("data/lotto.csv"):
        df = pd.DataFrame(columns=COLUMNS)
        print("Collecting previous draws")
        current_index = START_INDEX
        retry_count = 0
        while current_index != END_INDEX + 1:
            if retry_count == 10:
                if not df.empty:
                    print("Unable to connect to Lotto database to update data. Please try again later")
                    sys.exit(1)
                current_index += 1
                retry_count = 0
            for i in range(current_index, END_INDEX + 1):
                try:
                    add_lottto_data(df, i)
                    current_index = i + 1
                    retry_count = 0
                except:
                    print("Retrying connection...", end="\r")
                    current_index = i
                    retry_count += 1
                    break
        if not os.path.isdir("data"):
            os.makedirs("data")
        df.to_csv("data/lotto.csv")
    else:
        DATAFRAME = pd.read_csv("data/lotto.csv")
        DATAFRAME['drawDate'] = pd.to_datetime(DATAFRAME['drawDate'])
        app = dash.Dash(__name__, external_stylesheets=[dbc.themes.COSMO])
        create_dashboard(app)
        app.run_server(debug=True)
