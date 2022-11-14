# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     custom_cell_magics: kql
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.11.2
#   kernelspec:
#     display_name: venv_sp
#     language: python
#     name: python3
# ---

# %%
import json
from os import path
from glob import glob
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import numpy as np
from numpy import nan, where
from ratelimit import limits



# %%
# Instantiate Spotipy
cid = "ec23ca502beb44ffb22173b68cd37d9a"
secret = "556c805ce20848ed94194c081f0c96a8"
sp = spotipy.Spotify(
    client_credentials_manager=SpotifyClientCredentials(
        client_id=cid, client_secret=secret
    )
)


# %%
def key_to_camelot(df):
    df["key"] = (
        df["key"]
        .astype(str)
        .replace(
            {
                "-1": "no key detected",
                "0": "C",
                "1": "D-flat",
                "2": "D",
                "3": "E-flat",
                "4": "E",
                "5": "F",
                "6": "F-sharp",
                "7": "G",
                "8": "A-flat",
                "9": "A",
                "10": "B-flat",
                "11": "B",
            }
        )
    )

    df["mode"] = where(df["mode"] == 1, "major", "minor")
    df["key_signature"] = df["key"] + " " + df["mode"]

    key_to_wheel = {
        "A-flat minor": "1A",
        "B major": "1B",
        "E-flat minor": "2A",
        "F-sharp major": "2B",
        "B-flat minor": "3A",
        "D-flat major": "3B",
        "F minor": "4A",
        "A-flat major": "4B",
        "C minor": "5A",
        "E-flat major": "5B",
        "G minor": "6A",
        "B-flat major": "6B",
        "D minor": "7A",
        "F major": "7B",
        "A minor": "8A",
        "C major": "8B",
        "E minor": "9A",
        "G major": "9B",
        "B minor": "10A",
        "D major": "10B",
        "F-sharp minor": "11A",
        "A major": "11B",
        "D-flat minor": "12A",
        "E major": "12B",
    }

    # Convert diatonic key signatures to Camelot wheel equivalents.
    df["camelot"] = df["key_signature"].map(key_to_wheel)
    df = df.drop(columns=["key", "mode"])



# %%
def get_history():
    """_summary_
        Convert extended streaming history to DataFrame.

    Returns:
        _description_

    """
    json_concat = []
    history = glob(path.join("data", "endsong*.json"))
    for i in range(len(history)):

        if len(history) == 1:

            with open(path.join("data", "endsong.json"), encoding="utf-8") as json_file:
                user_json = json.load(json_file)
                json_concat.append(user_json)
        elif history:
            with open(
                path.join("data", f"endsong_{i}.json"), encoding="utf-8"
            ) as json_file:
                user_json = json.load(json_file)
                json_concat.append(user_json)
        elif not history:
            print(
                "No streaming history in the current working directory. Visit https://www.spotify.com/account/privacy/ to request your extended streaming history and move the endsong.json files to the notebook directory to run analyses on your extended history."
            )
            break
    df = (
        pd.DataFrame([j for i in json_concat for j in i])
        .drop(
            columns=[
                "username",
                "conn_country",
                "ip_addr_decrypted",
                "user_agent_decrypted",
                "platform",
                "incognito_mode",
                "offline_timestamp",
                "offline",
                "skipped",
            ]
        )
        #.fillna(value=False) # Todo: keep nan or no
        .rename(
            columns={
                "master_metadata_track_name": "track",
                "master_metadata_album_artist_name": "artist",
                "master_metadata_album_album_name": "album",
                "reason_start": "start",
                "reason_end": "end",
                "episode_name": "episode",
                "episode_show_name": "show",
                "spotify_track_uri": "id",
            }
        )
        .reset_index()
    )
    # Provide interoperability with API data, which uses "id" instead of "spotify_track_uri"
    df["ts"] = pd.to_datetime(df["ts"])
    df["date"] = df.ts.dt.strftime("%m/%d/%Y")
    df["time"] = df.ts.dt.strftime("%H:%M:%S")
    df["month"] = df.ts.dt.strftime("%m")
    df["year"] = df.ts.dt.strftime("%Y")

    return df


def remove_podcasts(df):
    # Drop podcast episodes. Reorder columns.
    df = (
        df#.fillna(value=nan) #Todo: keep nan or no
        .loc[df["episode"].isna()]
        .drop(
            columns=[
                "spotify_episode_uri",
                "episode",
                "show",
            ]
        )
    ).reset_index()
    return df

def get_podcasts(df):
    return df[df['id'] == False]#.fillna(value=nan) #Todo: keep nan or no



# %%
def open_wheel():
    with open(path.join("data", "camelot.json")) as json_file:
        camelot_json = json.load(json_file)
        wheel = camelot_json
        return wheel



# %%
@limits(calls=200, period=30)
def add_features(df, length=None, playlist=None):
    # Specify length for testing purposes
    df = df[:length]
    # Drop duplicates to limit API calls to include only unique URIs
    df_query = df.drop_duplicates(subset="id")
    offset_min = 0
    offset_max = 50
    af_res_list = []
    while True:
        if offset_min > len(df_query):
            af_res_list = [j for i in af_res_list for j in i]
            merge_cols = pd.DataFrame(af_res_list).loc[
                :, ["tempo", "duration_ms", "id", "key", "mode"]
            ]
            key_to_camelot(merge_cols)
            merge_cols = pd.merge(merge_cols, df)
            # Todo: separate function so we can remove these col names from streams_df too in get_history()
            merge_cols = merge_cols.rename(
                columns={
                    "master_metadata_track_name": "track",
                    "master_metadata_album_artist_name": "artist",
                    "master_metadata_album_album_name": "album",
                    "reason_start": "start",
                    "reason_end": "end",
                }
            )
            if playlist:
                merge_cols = merge_cols[
                    [
                        "artist",
                        "track",
                        "album",
                        "tempo",
                        "camelot",
                        "key_signature",
                        "id",
                    ]
                ]
            elif not playlist:
                merge_cols = merge_cols[
                    [
                        "artist",
                        "track",
                        "album",
                        "duration_ms",
                        "ms_played",
                        "date",
                        "time",
                        "month",
                        "year",
                        "tempo",
                        "camelot",
                        "key_signature",
                        "start",
                        "end",
                        "shuffle",
                        "id",
                        "ts",
                    ]
                ]
                merge_cols["date"] = merge_cols["date"].astype(str)
            # Round tempos to nearest whole number for easier. Playlist generation works with tempo ranges, so decimal precision is unnecessary.
            merge_cols["tempo"] = round(merge_cols["tempo"])
            return merge_cols
        res = sp.audio_features(
            df_query["id"].iloc[offset_min:offset_max],
        )
        if None not in res:
            af_res_list.append(res)
        else:
            res.remove(None)
            af_res_list.append(res)
        offset_min += 50
        offset_max += 50



# %%
def get_playlist(uri):
    playlist_df = []
    offset = 0
    while True:
        res = sp.playlist_tracks(
            uri,
            offset=offset,
            fields="items.track.id,items.track.artists,items.track.name,items.track.album,total",
        )
        if len(res["items"]) == 0:
            # Combine inner lists and exit loop
            # Todo: ask how this comprehension actually works
            playlist_df = [j for i in playlist_df for j in i]
            break
        playlist_df.append(res["items"])
        offset = offset + len(res["items"])
        print(offset, "/", res["total"])
    artist_dict = {"artist": [], "track": [], "id": [], "album": []}
    for i in range(len(playlist_df)):
        artist_dict["artist"].append(playlist_df[i]["track"]["artists"][0]["name"])
        artist_dict["track"].append(playlist_df[i]["track"]["name"])
        artist_dict["id"].append(playlist_df[i]["track"]["id"])
        artist_dict["album"].append(playlist_df[i]["track"]["album"]["name"])
    df = pd.DataFrame(artist_dict)
    return df



# %%
def pickl(df, name):
    return df.to_pickle(path.join("data", name))



# %%
def unpickl(*df):
    for name in df:
        yield pd.read_pickle(path.join("data", name))



# %%
def main():
    # Example playlist
    uri = "spotify:playlist:5CF6KvWn85N6DoWufOjP5T"
    # Todo: delete for production
    testlength = 1000

    all_streams = get_history()
    streams_df = remove_podcasts(all_streams)
    streams_af_df = add_features(streams_df, length=testlength)
    podcasts_df = get_podcasts(all_streams)
    playlist_af_df = add_features(get_playlist(uri), length=testlength, playlist=True)
    no_skip_df = streams_af_df.query("(ms_played / duration_ms) > 0.51").reset_index()

    pickl(streams_df, name="streams_df.p")
    pickl(streams_af_df, name="streams_af_df.p")
    pickl(no_skip_df, name="no_skip_df.p")
    pickl(playlist_af_df, name="playlist_af_df.p")
    pickl(podcasts_df, name="podcasts_df.p")
    # %store streams_df streams_af_df no_skip_df playlist_af_df podcasts_df


# %%
# if __name__ == "__main__":
#     main()


# %%
# # %prun -r main()

# %%
# # %store -r streams_af_df
