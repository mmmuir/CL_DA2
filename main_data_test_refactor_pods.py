import json
from glob import glob
from os import environ, path
from random import randint

import pandas as pd
import spotipy
from numpy import nan, where

# from ratelimit import limits
from spotipy.oauth2 import SpotifyClientCredentials

# Instantiate Spotipy.
# To run, assign your client ID and secret key to environment variables
# If environment variables names are SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET, you may
# omit assigning CID and SECRET variables and call SpotifyClientCredentials() without params,
# as shown in relevant docs https://spotipy.readthedocs.io/en/2.6.3/#client-credentials-flow

## For Windows:
# In PowerShell:
# $env:INSPECTIFY_CLIENT = '<key>'
# $env:INSPECTIFY_SECRET = '<key>'
# CID = environ['INSPECTIFY_CLIENT']
# SECRET = environ['INSPECTIFY_SECRET']

## For Linux:
# In Bash:
# export INSPECTIFY_CLIENT='<key>'
# export INSPECTIFY_SECRET='<key>'

## If you don't care about keeping secrets:
CID = 'ec23ca502beb44ffb22173b68cd37d9a'
SECRET = '556c805ce20848ed94194c081f0c96a8'
sp = spotipy.Spotify(
    client_credentials_manager=SpotifyClientCredentials(
        client_id=CID, client_secret=SECRET
    )
)


def get_history():
    """
    # Todo: add 'timezone' parameter for use by non-EST folks
    Concatenates endsong*.json files included in Spotify extended streaming history requests.
    Drops columns redacted by included remove_identifier.py script, and those unused by analysis functions.
    Truncates long column names. Converts timestamps to timezone-aware DateTime64 format.
    Adds additional datetime related columns for less verbose processing in Pandas.
    """
    json_concat = []
    history = glob(path.join('data', 'endsong*.json'))
    for i, file_path in enumerate(history):
        path.basename(file_path)

        if len(history) == 1:

            with open(path.join(file_path), encoding='utf-8') as json_file:
                user_json = json.load(json_file)
                json_concat.append(user_json)
        elif history:
            with open(path.join(file_path), encoding='utf-8') as json_file:
                user_json = json.load(json_file)
                json_concat.append(user_json)
        elif not history:
            print(
                'No streaming history in the current working directory. Visit https://www.spotify.com/account/privacy/\
                to request your extended streaming history and move the endsong.json files to data/ in the notebook\
                folder to run analyses on your extended history.'
            )
            break
    df = (
        pd.DataFrame([j for i in json_concat for j in i])
        .drop(
            columns=[
                'username',
                'conn_country',
                'ip_addr_decrypted',
                'user_agent_decrypted',
                'platform',
                'incognito_mode',
                'offline_timestamp',
                'offline',
                'skipped',
                'reason_start',
                'reason_end',
            ]
        )
        .fillna(value=nan)
    ).reset_index(drop=True)
    df.loc[df.spotify_episode_uri.isna(), 'media_type'] = 'music'
    df.loc[~df.spotify_episode_uri.isna(), 'media_type'] = 'podcast'

    df = df.rename(
        columns={
            'master_metadata_track_name': 'track',
            'master_metadata_album_artist_name': 'artist',
            'master_metadata_album_album_name': 'album',
            'spotify_track_uri': 'id',
            'spotify_episode_uri': 'id',
            'ms_played': 'playtime_s',
            'episode_name': 'track',
            'episode_show_name': 'artist',
            'ts': 'timestamp',
        }
    )
    df['id'].combine_first(df['id'])
    df['playtime_s'] = round(df.copy()['playtime_s'] / 1000).astype(int)
    df['playtime_m'] = round(df.copy()['playtime_s'] / 60, 2)
    df['playtime_h'] = round(df.copy()['playtime_m'] / 60, 2)
    df['timestamp'] = pd.to_datetime(df.copy()['timestamp'], utc=True)
    df['date'] = df.timestamp.dt.strftime('%m/%d/%Y')
    df['month'] = df.timestamp.dt.strftime('%b')
    df['year'] = df.timestamp.dt.strftime('%Y')
    df['day'] = df.timestamp.dt.strftime('%a')
    return df


print(get_history().head())
