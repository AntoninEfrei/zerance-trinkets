### Imports 
import requests
import pandas as pd
from concurrent.futures import as_completed, ProcessPoolExecutor
from requests_futures.sessions import FuturesSession
from requests.adapters import HTTPAdapter
import time
from urllib3.util.retry import Retry
from datetime import datetime
import traceback 

with open('api_key.txt', 'r') as file:
    api_key = file.read().strip()

def api_get_puuid(summonerId=None, gameName=None, tagLine=None, region='europe'):
    """Gets the puuid from a summonerId or riot_id and riot_tag

    Args:
        summonerId (str, optional): Summoner ID. Defaults to None.
        gameName (str, optional): Riot ID. Defaults to None.
        tagLine (str, optional): Riot Tag. Defaults to None.
        region (str, optional): Region. Defaults to 'americas'.

    Returns:
        str: puuid
    """
    print('Retrieving for:',gameName)

    if summonerId is not None:
        root_url = 'https://europe.api.riotgames.com/'
        endpoint = 'lol/summoner/v4/summoners/'

        response = requests.get(root_url+endpoint+summonerId+'?'+api_key)

        return response.json()['puuid']
    else:
        root_url = f'https://{region}.api.riotgames.com/'
        endpoint = f'riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}'
    
        response = requests.get(root_url+endpoint+'?'+api_key)
        if response.status_code == 429:
            print("Sleeping...")
            time.sleep(121)
            response = requests.get(root_url+endpoint+'?'+api_key)   
        try:               
            return response.json()['puuid']
        except KeyError as e:
            print('Puuid not retrieved, nickname must have changed')
            return None
      
def api_get_match_history_ids(puuid=None, region='europe', start=0, count=10):
    """Gets the match history ids for a given puuid.

    Args:
        puuid (str, optional): Player's puuid. Defaults to None.
        region (str, optional): Player's region. Defaults to 'americas'.
        start (int, optional): Match # start (for pagination). Defaults to 0.
        count (int, optional): How many matches per page. Defaults to 100.

    Returns:
        list: List of match ids.
    """

    try:
        root_url = f'https://{region}.api.riotgames.com'
        endpoint = f'/lol/match/v5/matches/by-puuid/{puuid}/ids'
        query_params = f'?&start={start}&count={count}'

        
        while True:
            response = requests.get(root_url+endpoint+query_params+'&'+api_key)
            if response.status_code == 429:  # Rate limit exceeded
                retry_after = int(response.headers.get('Retry-After', 10))  # Default to 10 seconds
                print(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
                time.sleep(retry_after)
            elif response.status_code == 200:  # Request successful
                return response.json()
            else:
                print(f"Unexpected status code: {response.status_code}. Retrying...")
                time.sleep(5)  # Wait for 5 seconds before retrying
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
def process_match_json_reporting(match_json):
    """Processes the match json into a dataframe.

    Args:
        match_json (dict): Match JSON.
        puuid (str): Player's puuid.

    Returns:
        dataframe: Dataframe of the processed match data.
    """
    side_dict = {
        100:'blue',
        200:'red'
    }
    info = match_json['info']
    metadata = match_json['metadata']
    matchId = metadata['matchId']
    participants = metadata['participants']
    
    matchDFs = pd.DataFrame()
    
    for player_puuid in participants:
             
        player = info['participants'][participants.index(player_puuid)]

        #get opponent champion 
        for other_player in info['participants']:
            if other_player['teamPosition'] == player['teamPosition'] and other_player['championName'] != player['championName']:
                opp_champion = other_player['championName']
            else:
                opp_champion = None 

        gameCreation = info['gameCreation']
        gameStartTimestamp = info['gameStartTimestamp']
        gameEndTimestamp = info['gameEndTimestamp']
        timePlayed = gameEndTimestamp-gameStartTimestamp
        gameMode = info['gameMode']
        gameVersion = info['gameVersion']
        platformId = info['platformId']
        queueId = info['queueId']
        puuid = player['puuid']
        riotIdGameName = player['summonerName']
        try:
            riotIdTagLine = player['riotIdTagline']
        except:
            riotIdTagLine = ''
        side = side_dict[player['teamId']]
        win = player['win']

        champion = player['championName']
        kills = player['kills']
        deaths = player['deaths']
        assists = player['assists']
        summOne = player['summoner1Id']
        summTwo = player['summoner2Id']
        earlySurrender = player['gameEndedInEarlySurrender']
        surrender = player['gameEndedInSurrender']
        firstBlood = player['firstBloodKill']
        firstBloodAssist = player['firstBloodAssist']
        firstTower = player['firstTowerKill']
        firstTowerAssist = player['firstTowerAssist']
        dragonKills = player['dragonKills']

        damageDealtToBuildings = player['damageDealtToBuildings']
        damageDealtToObjectives = player['damageDealtToObjectives']
        damageSelfMitigated = player['damageSelfMitigated']
        goldEarned = player['goldEarned']
        teamPosition = player['teamPosition']
        lane = player['lane']
        largestKillingSpree = player['largestKillingSpree']
        longestTimeSpentLiving = player['longestTimeSpentLiving']
        objectivesStolen = player['objectivesStolen']
        totalMinionsKilled = player['totalMinionsKilled']
        totalAllyJungleMinionsKilled = player['totalAllyJungleMinionsKilled']
        totalEnemyJungleMinionsKilled = player['totalEnemyJungleMinionsKilled']
        totalNeutralMinionsKilled = totalAllyJungleMinionsKilled + totalEnemyJungleMinionsKilled
        totalDamageDealtToChampions = player['totalDamageDealtToChampions']
        totalDamageShieldedOnTeammates = player['totalDamageShieldedOnTeammates']
        totalHealsOnTeammates = player['totalHealsOnTeammates']
        totalDamageTaken = player['totalDamageTaken']
        totalTimeCCDealt = player['totalTimeCCDealt']
        totalTimeSpentDead = player['totalTimeSpentDead']
        turretKills = player['turretKills']
        turretsLost = player['turretsLost']
        visionScore = player['visionScore']
        controlWardsPlaced = player['detectorWardsPlaced']
        wardsKilled = player['wardsKilled']
        wardsPlaced = player['wardsPlaced']

        item0 = player['item0']
        item1 = player['item1']
        item2 = player['item2']
        item3 = player['item3']
        item4 = player['item4']
        item5 = player['item5']
        item6 = player['item6']
        try:
            perks = player['perks']

            perkKeystone = perks['styles'][0]['selections'][0]['perk']
            perkPrimaryRow1 = perks['styles'][0]['selections'][1]['perk']
            perkPrimaryRow2 = perks['styles'][0]['selections'][2]['perk']
            perkPrimaryRow3 = perks['styles'][0]['selections'][3]['perk']
            perkPrimaryStyle = perks['styles'][0]['style']
            perkSecondaryRow1 = perks['styles'][1]['selections'][0]['perk']
            perkSecondaryRow2 = perks['styles'][1]['selections'][1]['perk']
            perkSecondaryStyle = perks['styles'][1]['style']
            perkShardDefense = perks['statPerks']['defense']
            perkShardFlex = perks['statPerks']['flex']
            perkShardOffense = perks['statPerks']['offense']
        except:
            perkKeystone = ''
            perkPrimaryRow1 = ''
            perkPrimaryRow2 = ''
            perkPrimaryRow3 = ''
            perkPrimaryStyle = ''
            perkSecondaryRow1 = ''
            perkSecondaryRow2 = ''
            perkSecondaryStyle = ''
            perkShardDefense = ''
            perkShardFlex = ''
            perkShardOffense = ''


        matchDF = pd.DataFrame({
            'match_id': [matchId],
            'participants': [participants],
            'game_creation': [gameCreation],
            'game_start_timestamp': [gameStartTimestamp],
            'game_end_timestamp': [gameEndTimestamp],
            'game_version': [gameVersion],
            'queue_id': [queueId],
            'game_mode': [gameMode],
            'platform_id': [platformId],
            'puuid': [puuid],
            'riot_id': [riotIdGameName],
            'riot_tag': [riotIdTagLine],
            'time_played': [timePlayed],
            'side': [side],
            'win': [win],
            'team_position': [teamPosition],
            'lane': [lane],
            'champion': [champion],
            'kills': [kills],
            'deaths': [deaths],
            'assists': [assists],
            'summoner1_id': [summOne],
            'summoner2_id': [summTwo],
            'gold_earned': [goldEarned],
            'total_minions_killed': [totalMinionsKilled],
            'total_neutral_minions_killed': [totalNeutralMinionsKilled],
            'total_ally_jungle_minions_killed': [totalAllyJungleMinionsKilled],
            'total_enemy_jungle_minions_killed': [totalEnemyJungleMinionsKilled],
            'early_surrender': [earlySurrender],
            'surrender': [surrender],
            'first_blood': [firstBlood],
            'first_blood_assist': [firstBloodAssist],
            'first_tower': [firstTower],
            'first_tower_assist': [firstTowerAssist],
            'damage_dealt_to_buildings': [damageDealtToBuildings],
            'turret_kills': [turretKills],
            'turrets_lost': [turretsLost],
            'damage_dealt_to_objectives': [damageDealtToObjectives],
            'dragonKills': [dragonKills],
            'objectives_stolen': [objectivesStolen],
            'longest_time_spent_living': [longestTimeSpentLiving],
            'largest_killing_spree': [largestKillingSpree],
            'total_damage_dealt_champions': [totalDamageDealtToChampions],
            'total_damage_taken': [totalDamageTaken],
            'total_damage_self_mitigated': [damageSelfMitigated],
            'total_damage_shielded_teammates': [totalDamageShieldedOnTeammates],
            'total_heals_teammates': [totalHealsOnTeammates],
            'total_time_crowd_controlled': [totalTimeCCDealt],
            'total_time_spent_dead': [totalTimeSpentDead],
            'vision_score': [visionScore],
            'wards_killed': [wardsKilled],
            'wards_placed': [wardsPlaced],
            'control_wards_placed': [controlWardsPlaced],
            'item0': [item0],
            'item1': [item1],
            'item2': [item2],
            'item3': [item3],
            'item4': [item4],
            'item5': [item5],
            'item6': [item6],
            'perk_keystone': [perkKeystone],
            'perk_primary_row_1': [perkPrimaryRow1],
            'perk_primary_row_2': [perkPrimaryRow2],
            'perk_primary_row_3': [perkPrimaryRow3],
            'perk_secondary_row_1': [perkSecondaryRow1],
            'perk_secondary_row_2': [perkSecondaryRow2],
            'perk_primary_style': [perkPrimaryStyle],
            'perk_secondary_style': [perkSecondaryStyle],
            'perk_shard_defense': [perkShardDefense],
            'perk_shard_flex': [perkShardFlex],
            'perk_shard_offense': [perkShardOffense],
            'opp_champion': [opp_champion],

        })
        matchDFs = pd.concat([matchDFs,matchDF]) 
    return matchDFs

def api_get_match_history_puuid(list_puuid, region='europe', debug=False, reporting_focus = False):
    
    """Gets the match history for a given riot_id and riot_tag.

    Args:
        list_puuid(list): Player's puuid. One for each team.
        region (str, optional): Player's region. Defaults to 'americas'.
        debug (bool, optional): Whether or not to print out matchIds as they are processed. Defaults to False.
        reporting_focus (bool, optional): Whether or not to focus on only picks and winrate. Defaults to False.

    Returns:
        DataFrame: DataFrame of all matches.
    """

    # Set up a session with retry mechanisms
    session = FuturesSession(executor=ProcessPoolExecutor(max_workers=10))
    retries = 5
    status_forcelist = [429]
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        respect_retry_after_header=True,
        status_forcelist=status_forcelist,
    )

    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    list_matchIds = []
    for player_puuid in list_puuid:
        print(player_puuid)
        matchIds = api_get_match_history_ids(puuid=player_puuid)
        for id in matchIds: #append the value to the list_matchIds and not lists
            list_matchIds.append(id)

    print('Nombre de matchs avec doublons:',len(list_matchIds))
    print('Nombre de matchs sans doublons:',len(list(set(list_matchIds))))

    df = pd.DataFrame()
    list_matchIds = list(set(list_matchIds))

    if len(list_matchIds) > 0:

        # If there are new matches to process, create asynchronous requests for match data
        futures = [session.get(f'https://{region}.api.riotgames.com/lol/match/v5/matches/{matchId}' + '?' + api_key) for matchId in list_matchIds]

        i = 0

        # Iterate through completed asynchronous requests
        for future in as_completed(futures):
            resp = future.result()
            try:
                x = resp.json()['metadata']['matchId']
            except : 
                    print('Answer :', resp.json())
                
            if debug:
                # If debug is enabled, print match processing information
                t1 = time.time()
                df = pd.concat([df, process_match_json_reporting(resp.json())])

                t2 = time.time()
                
                print('a',resp.json()['metadata']['matchId'] + f' - {i} ({round(t2 - t1, 2)}s)')
         
                i += 1
            else:
                df = pd.concat([df, process_match_json_reporting(resp.json())])
                    

        try:# Return the DataFrame containing information about the fetched matches
            df['game_creation'] = pd.to_datetime(df['game_creation'], unit='ms')
            df['game_start_timestamp'] = pd.to_datetime(df['game_start_timestamp'], unit='ms')
            df['game_end_timestamp'] = pd.to_datetime(df['game_end_timestamp'], unit='ms')
            df['time_played'] = df['time_played']/60000
        except: 
            None
        return df
    else:
        # If there are no new matches to process, print a message and return an empty DataFrame
        print(f'No matches')
        return pd.DataFrame()