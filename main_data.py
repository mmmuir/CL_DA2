import json
from glob import glob
from os import environ, path
from random import randint

import pandas as pd
import spotipy
from numpy import nan, where
from ratelimit import limits
from spotipy.oauth2 import SpotifyClientCredentials

# Instantiate Spotipy.
# To run, assign your client ID and secret key to environment variables
# If environment variables names are SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET, you may
# omit assigning CID and SECRET variables and call SpotifyClientCredentials() without params,
# as shown in relevant docs https://spotipy.readthedocs.io/en/2.6.3/#client-credentials-flow

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
        .rename(
            columns={
                'master_metadata_track_name': 'track',
                'master_metadata_album_artist_name': 'artist',
                'master_metadata_album_album_name': 'album',
                'spotify_track_uri': 'id',
                'ms_played': 'playtime_s',
                'episode_name': 'episode',
                'episode_show_name': 'show',
                'ts': 'timestamp',
            }
        )
        .reset_index(drop=True)
    )
    df['playtime_s'] = round(df.copy()['playtime_s'] / 1000).astype(int)
    df['playtime_m'] = round(df.copy()['playtime_s'] / 60, 2)
    df['playtime_h'] = round(df.copy()['playtime_m'] / 60, 2)
    # Todo: fix timezone localization issue, now broken. Possible compatibility issue after upgrading?
    df['timestamp'] = pd.to_datetime(df.copy()['timestamp'], utc=True).dt.tz_convert(
        'EST'
    )
    df['date'] = df.timestamp.dt.strftime('%m/%d/%Y')
    df['month'] = df.timestamp.dt.strftime('%b')
    df['year'] = df.timestamp.dt.strftime('%Y')
    df['day'] = df.timestamp.dt.strftime('%a')
    return df


def get_pods(df):
    """
    args:
        df: A DataFrame created by get_history() before processing with add_features()
    returns:
        df: A DataFrame containing only podcasts. Works by dropping rows with non-null 'id' column, previously derived from music-only 'spotify_track_uri' columns. 'spotify_episode_uri' is then renamed to 'id' to allow for simultaneous uri-based queries on podcast and music entries.
    # Todo: just drop based on track_uri, rename both columns and remerge or something. currently not the same in all_streams
    """
    # Extract podcasts from all_streams.
    return (
        df[df['id'].isnull()]
        .reset_index(drop=True)
        .drop(columns=['track', 'artist', 'album', 'shuffle', 'id'])
        .rename(
            columns={'show': 'artist', 'episode': 'track', 'spotify_episode_uri': 'id'}
        )
    )


def remove_pods(df):
    """
    args:
        df: A DataFrame created by get_history(). Removes podcast episodes by selecting rows with null 'episode' columns.
        Drops rows containing 'myNoise' in df.artist -- these are headphone test tracks.
    """
    # Drop podcast episodes. Reorder columns.
    df = (
        df.fillna(value=nan)
        .loc[df['episode'].isna()]
        .drop(columns=['spotify_episode_uri', 'episode', 'show'])
        .loc[df['artist'].str.contains('myNoise') == False]
        .reset_index(drop=True)
    )
    return df


def get_playlist(uri):
    """
    args:
        uri: The URI for a public Spotify playlist.
    returns:
        df: A DataFrame of the chosen playlist.
        # Todo: add 'fields' and 'dtypes' to all docstrings
    """
    playlist_df = []
    offset = 0
    while True:
        res = sp.playlist_tracks(
            uri,
            offset=offset,
            fields='items.track.id,items.track.artists,items.track.name,items.track.album,total',
        )
        if len(res['items']) == 0:
            # Combine inner lists and exit loop
            playlist_df = [j for i in playlist_df for j in i]
            break
        playlist_df.append(res['items'])
        offset = offset + len(res['items'])
        print(offset, '/', res['total'])
    artist_dict = {'artist': [], 'track': [], 'id': [], 'album': []}
    for i, song in enumerate(playlist_df):
        artist_dict['artist'].append(song['track']['artists'][0]['name'])
        artist_dict['track'].append(song['track']['name'])
        artist_dict['id'].append(song['track']['id'])
        artist_dict['album'].append(song['track']['album']['name'])
    df = pd.DataFrame(artist_dict)
    return df


def open_wheel():
    """returns: A DataFrame containing key signature transformations from the Camelot wheel."""
    with open(path.join('data', 'camelot.json'), encoding='utf-8') as json_file:
        camelot_json = json.load(json_file)
        camelot_wheel = pd.DataFrame.from_dict(camelot_json)
        return camelot_wheel


def key_to_camelot(df):
    """
    args:
        df: A DataFrame containing Spotify audio features. Can be applied to a raw audio_features() response, or a DataFrame that has already been enriched by add_features().
    Converts Spotify's integer-based key/mode designators into Camelot wheel equivalents
    """
    df['key'] = (
        df['key']
        .astype(str)
        .replace(
            {
                '-1': 'no key detected',
                '0': 'C',
                '1': 'D-flat',
                '2': 'D',
                '3': 'E-flat',
                '4': 'E',
                '5': 'F',
                '6': 'F-sharp',
                '7': 'G',
                '8': 'A-flat',
                '9': 'A',
                '10': 'B-flat',
                '11': 'B',
            }
        )
    )

    df['mode'] = where(df['mode'] == 1, 'major', 'minor')
    df['key_signature'] = df['key'] + ' ' + df['mode']

    wheel_df = open_wheel().iloc[0]

    # Convert diatonic key signatures to Camelot wheel equivalents.
    df['camelot'] = df['key_signature'].map(
        lambda x: wheel_df.loc[wheel_df == x].index[0]
    )
    df = df.drop(columns=['key', 'mode'])


@limits(calls=150, period=30)
def add_features(df, length=None, playlist=None):
    """
    Adds audio features to a DataFrame by querying the API to add information such as tempo, key signature, and track duration.
    args:
        df: A DataFrame with no audio features.
    params:
        length: How much of the original dataframe to add audio features to. Intended testing purposes to limit API calls.
    playlist: If True, merges only columns returned by get_playlist().
    Returns: A DataFrame with audio features.
    """
    # Specify length in main() for testing purposes
    df = df[:length]
    # Drop duplicates to limit API calls to include only unique URIs
    df_query = df.drop_duplicates(subset='id')
    offset_min = 0
    offset_max = 50
    af_res_list = []
    while True:
        if offset_min > len(df_query):
            af_res_list = [j for i in af_res_list for j in i]
            merge_cols = (
                pd.DataFrame(af_res_list)
                .loc[:, ['tempo', 'duration_ms', 'id', 'key', 'mode']]
                .rename(
                    columns={
                        'master_metadata_track_name': 'track',
                        'master_metadata_album_artist_name': 'artist',
                        'master_metadata_album_album_name': 'album',
                        'reason_start': 'start',
                        'reason_end': 'end',
                        'duration_ms': 'duration',
                        'ms_played': 'playtime_s',
                        'ts': 'timestamp',
                    }
                )
            )

            key_to_camelot(merge_cols)
            merge_cols = pd.merge(merge_cols, df)
            # : separate function so we can remove these col names from music_streams_no_features too in get_history()
            if playlist:
                merge_cols = merge_cols[
                    [
                        'artist',
                        'track',
                        'album',
                        'tempo',
                        'camelot',
                        'key_signature',
                        'id',
                        'duration',
                    ]
                ]
            elif not playlist:
                merge_cols = merge_cols[
                    [
                        'artist',
                        'track',
                        'album',
                        'duration',
                        'playtime_m',
                        'date',
                        'day',
                        'month',
                        'year',
                        'tempo',
                        'camelot',
                        'key_signature',
                        'shuffle',
                        'id',
                        'timestamp',
                        'playtime_s',
                        'playtime_h',
                    ]
                ]
            # Round tempos to nearest whole number for easier. Playlist generation works with tempo ranges, so decimal precision is unnecessary.
            merge_cols['duration'] = round(merge_cols['duration'].copy() / 1000).astype(
                int
            )
            merge_cols['tempo'] = round(merge_cols['tempo']).astype(int)
            return merge_cols
        res = sp.audio_features(df_query['id'].iloc[offset_min:offset_max])
        if None not in res:
            af_res_list.append(res)
        else:
            res.remove(None)
            af_res_list.append(res)
        offset_min += 50
        offset_max += 50


def get_friendly(
    df, tempo_range=10, uri=None, index=None, shuffle=None, shifts=['all']
):
    """
    args:
        df: A DataFrame with audio features added.
    params:
        tempo_range: Default 10. The tempo range of returned tracks, +/- the tempo of the input track.
        uri: Default None. The ID of the track in the input df user wishes to find compatible songs for.
        index: Default None. The index of the track in the input df user wishes to find compatible songs for.
        Shuffle: Default None. If True, tracks with compatible keys will be returned for a random track from input df
        shifts: Type: List. Which shifts to include.
    Returns: A DataFrame of tracks from the original DataFrame whose key signatures are included in the desired 'shifts'
             in relation to the input track's key signature.

    Args:
        tempo_range (object):
    """
    wheel = open_wheel()
    df = df.drop_duplicates(subset='id').reset_index()
    if uri:
        song_selected = df.loc[df['id'] == uri].iloc[0]
    elif index or index == 0:
        song_selected = df.loc[index]
    elif shuffle:
        song_selected = df.iloc[randint(0, len(df) - 1)]
    else:
        print(
            'Error: no song selected. Specify shuffle=True to operate on random song.'
        )
    # Designate desired tempo range
    selected_tempo = song_selected['tempo']
    acceptable_tempos = range(
        (selected_tempo - tempo_range), (selected_tempo + tempo_range), 1
    )

    # Select harmonically compatible key signatures in camelot.json
    friendly_keys = []
    for i, shift in enumerate(shifts):
        key = wheel[song_selected['camelot']][shift]
        friendly_keys.append(key)
        if type(key) == list:
            friendly_keys.extend(key)

    # Show tracks with harmonically compatible key signatures within a given tempo range. Accounts for Spotify's tendency to double or halve numeric tempos.

    return df.query(
        'camelot in @friendly_keys & (tempo in @acceptable_tempos | tempo * 2 in @acceptable_tempos | tempo / 2 in @acceptable_tempos)'
    )


def df_to_json(df, name):
    """
    args:
        df: DataFrame to store as JSON.
        name: Filename of returned JSON.
    returns:
        Writes a JSON version of dataframe to 'data/' folder.
    """
    return df.to_json(path.join('data', name))


def json_to_df(*df):
    """
    args:
        *dfs: Multiple DataFrames.
    returns: Multiple DataFrames to be assigned to multiple variables. for a single DataFrame, just use pd.read_json(). intended for unpacking many dfs at once
    """
    for name in df:
        yield pd.read_json(path.join('data', name))


def main():
    # Example playlist
    uri = 'spotify:playlist:5CF6KvWn85N6DoWufOjP5T'
    testlength = None

    all_streams = get_history()
    podcasts = get_pods(all_streams)
    music_streams_no_features = remove_pods(all_streams)
    music_streams = add_features(music_streams_no_features, length=testlength)
    playlist_example = add_features(get_playlist(uri), length=testlength, playlist=True)
    no_skip_df = music_streams.query('(playtime_s / duration) > 0.75').reset_index(
        drop=True
    )
    wheel_df = open_wheel()

    df_to_json(podcasts, name='podcasts.json')
    df_to_json(all_streams, name='all_streams.json')
    df_to_json(music_streams_no_features, name='music_streams_no_features.json')
    df_to_json(music_streams, name='music_streams.json')
    df_to_json(no_skip_df, name='no_skip_df.json')
    df_to_json(playlist_example, name='playlist_example.json')
    df_to_json(wheel_df, name='wheel_df.json')


if __name__ == '__main__':
    main()
