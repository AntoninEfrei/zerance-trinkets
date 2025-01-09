from riot_functions import *
import pandas as pd
import json
from datetime import datetime
import traceback
from supabase import create_client, Client
from configparser import ConfigParser
import multiprocessing

def main():

    parser = ConfigParser()
    parser.read('config.ini')

    # get keys 
    url = str(parser.get('supabase', 'SUPABASE_URL'))
    key= str(parser.get('supabase', 'SUPABASE_KEY'))
    api_key = str(parser.get('riot_api', 'api_key'))
    api_key = "api_key="+api_key

    supabase: Client = create_client(url, key)


    # list of nicknames 
    list_nickname = ['Spiritual Realm#Shy','jué ji#00097','cant hold me#zeb','13 김수환#K13','enjawve#EUW']

    def nicknames_to_gamename_tagline(list_nicknames : list):
        """
        Converts a list of nicknames in the format 'gameName#tagLine' 
        to a list of puuid by splitting in # and using
        api_get_puuid function from riot_function.py'.

        Args:
            list_nicknames (list): A list of nicknames in the format 'gameName#tagLine'.

        Returns:
            list: A list of puuids.
        """ 

        list_puuid = []
        for nickname in list_nicknames:
            gameName, tagLine = nickname.split("#")
            puuid = api_get_puuid(gameName = gameName,tagLine = tagLine)
            list_puuid.append(puuid)
        return list_puuid

    # get puuid as list of players
    list_puuid_players = nicknames_to_gamename_tagline(list_nickname)
    # get df of all games they played
    df_games = api_get_match_history_puuid(list_puuid_players)

    def from_df_to_db(df : pd.DataFrame, table = None):
        '''
        Function that convert a df indexed to 0 right index according to db
        & put it 
        '''
        df.reset_index(drop=True, inplace = True)
        df.reset_index(drop=False,inplace = True) 
        try : 
            starting_index = supabase.table('game_player').select('index').order("index", desc=True).execute().data[0]['index'] #get the latest index in db
        except IndexError as e:
            starting_index = 0
            
        
        # Update the "index" column
        df['index'] = range(starting_index, starting_index + len(df))

        def epoch_to_iso(epoch_time):
            return datetime.utcfromtimestamp(epoch_time / 1000).isoformat() + 'Z'

        for i in range(len(df)-1):
            json_row = df.iloc[i].to_json()
            json_row = json.loads(json_row)
            try:
                transformed_data = {
                **json_row,  # Start with the base JSON
                'game_creation': epoch_to_iso(json_row['game_creation']),
                'game_start_timestamp': epoch_to_iso(json_row['game_start_timestamp']),
                'game_end_timestamp': epoch_to_iso(json_row['game_end_timestamp']),
                }
                # Attempt to insert data into the database
                supabase.table(table).insert(transformed_data).execute()

            except Exception as e:
                # Log the exception and row index
                print(f"Failed to insert row {i}. Reason: {str(e)}")
                # Optionally, print the stack trace for debugging
                traceback.print_exc()

    from_df_to_db(df_games,'game_player')

if __name__ == '__main__':
    # Make sure to use this idiom to avoid issues with multiprocessing
    multiprocessing.set_start_method('spawn')  # Optional if you want to set the start method explicitly
    main()
    
## FIXME : check for duplicates match_id from db to not waste time -> make a query to db in list_match_ids? | check for the issue about not having 10 rows for all match_id in db
