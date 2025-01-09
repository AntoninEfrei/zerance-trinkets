import datetime
import random
from riot_functions import *
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from configparser import ConfigParser
parser = ConfigParser()
parser.read('config.ini')

supabase: Client = create_client(url, key)

############## Functions 

def path_to_image_html(path): #crédit mascode 
    '''
     This function essentially convert the image url to 
     '<img src="'+ path + '"/>' format. And one can put any
     formatting adjustments to control the height, aspect ratio, size etc.
     within as in the below example. 
    '''

    return '<img src="'+ path + '" style="max-height:50px;"/>'

############## Global variables 
list_teams = ["lille esport",
              "esprit shonen",
              "zerance",
              "karmine corp blue stars",
              "valiant",
              "project conquerors",
              "skillcamp",
              "izidream"]
list_roles = ['TOP','JUNGLE','MIDDLE','BOTTOM','UTILITY']


############## APP ##############

# Show app title and description.
st.set_page_config(page_title="Zerance Trinkets", page_icon="🎫")
st.title(" Zerance Trinkets")

## select box teams 
selected_team = st.selectbox("Select a team (ONLY LILLE AVAILABLE)", list_teams)

# get active players from select team 
r = supabase.table('players').select('player_nickname,main_puuid').eq('current_team',selected_team).execute()

# get puuid / nicknames lists
list_puuid = []
list_nickname = []
for dict_player in r.data:
    list_puuid.append(dict_player['main_puuid'])
    list_nickname.append(dict_player['player_nickname'])


### get soloq from select players
r = supabase.table('games_player').select('*').in_('puuid',list_puuid).execute()
df_players = pd.DataFrame(r.data)



st.markdown(f'<h2 class="title">Pick History from {selected_team}</h2>', unsafe_allow_html=True)
col1, col2, col3, col4, col5 = st.columns([5, 5, 5, 5, 5])
columns = [col1, col2, col3, col4, col5]


for role, col, puuid, nickname in zip(list_roles, columns, list_puuid, list_nickname):

                #get the  winrate for each role
                df_player = df_players[(df_players['puuid'] == puuid) & (df_players['team_position'] == role)]

                win_rates = df_player.groupby('champion')['win'].agg(['mean', 'size'])  # Aggregate mean and count
                win_rates.columns = ['W/R', 'games']
                win_rates['W/R'] = (win_rates['W/R'] * 100).round(2)
                win_rates = win_rates.sort_values(by='games', ascending=False)
                st.write(win_rates)
                #display images
                win_rates = win_rates.reset_index(drop = False)
                win_rates['Champ'] = "https://ddragon.leagueoflegends.com/cdn/15.1.1/img/champion/" + win_rates['champion'] + ".png"
                win_rates.drop(columns=['champion'], inplace = True)
                columns = ['Champ'] + [col for col in win_rates.columns if col != 'Champ']
                win_rates = win_rates[columns]   
                win_rates = win_rates.style.format({"Champ":path_to_image_html, "W/R": lambda x: f"{x:.1f}"})
                win_rates = win_rates.hide(axis = "index")
                win_rates = win_rates.to_html(escape = False)
                
                #display titles for each position 
                with col:
                    st.write(f"##### {role[0] + role[1:].lower()}: {nickname}")
                    st.markdown(win_rates, unsafe_allow_html= True)
        
