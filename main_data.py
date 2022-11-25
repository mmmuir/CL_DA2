import json
from os import path
from glob import glob
from random import randint
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
from numpy import nan, where
from ratelimit import limits


# Instantiate Spotipy
CID = "ec23ca502beb44ffb22173b68cd37d9a"
SECRET = "secret_key_here"
sp = spotipy.Spotify(
    client_credentials_manager=SpotifyClientCredentials(
        client_id=CID, client_secret=SECRET
    )
)


def get_history():
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
                "No streaming history in the current working directory. Visit https://www.spotify.com/account/privacy/ to request\
                 your extended streaming history and move the endsong.json files to data/ in the notebook folder to run analyses on your extended history."
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
                "reason_start",
                "reason_end",
            ]
        )
        .rename(
            columns={
                "master_metadata_track_name": "track",
                "master_metadata_album_artist_name": "artist",
                "master_metadata_album_album_name": "album",
                "spotify_track_uri": "id",
                "ms_played": "playtime_s",
                "episode_name": "episode",
                "episode_show_name": "show",
                "ts": "timestamp",
            }
        )
        .reset_index(drop=True)
    )
    df["playtime_s"] = round(df.copy()["playtime_s"] / 1000).astype(int)
    df["playtime_m"] = round(df.copy()["playtime_s"] / 60, 2)
    df["playtime_h"] = round(df.copy()["playtime_m"] / 60, 2)
    # Todo: fix timezone localization issue, now broken. Possible compatibility issue after upgrading?
    df["timestamp"] = pd.to_datetime(df.copy()["timestamp"], utc=True).dt.tz_convert(
        "EST"
    )
    df["date"] = df.timestamp.dt.strftime("%m/%d/%Y")
    df["month"] = df.timestamp.dt.strftime("%b")
    df["year"] = df.timestamp.dt.strftime("%Y")
    df["day"] = df.timestamp.dt.strftime("%a")
    return df


def get_pods(df):
    # Extract podcasts from all_streams.
    return (
        df[df["id"].isnull()]
        .reset_index(drop=True)
        .drop(columns=["track", "artist", "album", "shuffle", "id"])
        .rename(
            columns={"show": "artist", "episode": "track", "spotify_episode_uri": "id"}
        )
    )


def remove_pods(df):
    # Drop podcast episodes. Reorder columns.
    df = (
        (
            df.fillna(value=nan)
            .loc[df["episode"].isna()]
            .drop(
                columns=[
                    "spotify_episode_uri",
                    "episode",
                    "show",
                ]
            )
        )
        .reset_index(drop=True)
        .loc[df["artist"].str.contains("myNoise") == False]
    )
    return df


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


def open_wheel():
    with open(path.join("data", "camelot.json"), encoding="utf-8") as json_file:
        camelot_json = json.load(json_file)
        camelot_wheel = pd.DataFrame.from_dict(camelot_json)
        return camelot_wheel


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

    wheel_df = open_wheel().iloc[0]

    # Convert diatonic key signatures to Camelot wheel equivalents.
    df["camelot"] = df["key_signature"].map(
        lambda x: wheel_df.loc[wheel_df == x].index[0]
    )
    df = df.drop(columns=["key", "mode"])


@limits(calls=150, period=30)
def add_features(df, length=None, playlist=None):
    # Specify length in main() for testing purposes
    df = df[:length]
    # Drop duplicates to limit API calls to include only unique URIs
    df_query = df.drop_duplicates(subset="id")
    offset_min = 0
    offset_max = 50
    af_res_list = []
    while True:
        if offset_min > len(df_query):
            af_res_list = [j for i in af_res_list for j in i]
            merge_cols = (
                pd.DataFrame(af_res_list)
                .loc[:, ["tempo", "duration_ms", "id", "key", "mode"]]
                .rename(
                    columns={
                        "master_metadata_track_name": "track",
                        "master_metadata_album_artist_name": "artist",
                        "master_metadata_album_album_name": "album",
                        "reason_start": "start",
                        "reason_end": "end",
                        "duration_ms": "duration",
                        "ms_played": "playtime_s",
                        "ts": "timestamp",
                    }
                )
            )

            key_to_camelot(merge_cols)
            merge_cols = pd.merge(merge_cols, df)
            # : separate function so we can remove these col names from music_streams_no_features too in get_history()
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
                        "duration",
                    ]
                ]
            elif not playlist:
                merge_cols = merge_cols[
                    [
                        "artist",
                        "track",
                        "album",
                        "duration",
                        "playtime_m",
                        "date",
                        "day",
                        "month",
                        "year",
                        "tempo",
                        "camelot",
                        "key_signature",
                        "shuffle",
                        "id",
                        "timestamp",
                        "playtime_s",
                        "playtime_h",
                    ]
                ]
            # Round tempos to nearest whole number for easier. Playlist generation works with tempo ranges, so decimal precision is unnecessary.
            merge_cols["duration"] = round(merge_cols["duration"].copy() / 1000).astype(
                int
            )
            merge_cols["tempo"] = round(merge_cols["tempo"]).astype(int)
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


def get_friendly(
    df,
    tempo_range=10,
    uri=None,
    index=None,
    shuffle=None,
    shift=["all"],
):
    wheel = open_wheel()
    df = df.drop_duplicates(subset="id").reset_index()
    if uri:
        song_selected = df.loc[df["id"] == uri].iloc[0]
    elif index or index == 0:
        song_selected = df.loc[index]
    elif shuffle:
        song_selected = df.iloc[randint(0, len(df) - 1)]
    else:
        print(
            "Error: no song selected. Specify shuffle=True to operate on random song."
        )
    # Designate desired tempo range
    selected_tempo = song_selected["tempo"]
    acceptable_tempos = range(
        (selected_tempo - tempo_range), (selected_tempo + tempo_range), 1
    )

    # Select harmonically compatible key signatures in camelot.json
    friendly_keys = []
    for i in range(len(shift)):
        key = wheel[song_selected["camelot"]][shift[i]]
        friendly_keys.append(key)
        if type(key) == list:
            friendly_keys.extend(key)

    # Show tracks with harmonically compatible key signatures within a given tempo range. Accounts for Spotify's tendency to double or halve numeric tempos.

    return df.query(
        "camelot in @friendly_keys & (tempo in @acceptable_tempos | tempo * 2 in @acceptable_tempos | tempo / 2 in @acceptable_tempos)"
    )


def df_to_json(df, name):
    return df.to_json(path.join("data", name))


def json_to_df(*df):
    for name in df:
        yield pd.read_json(path.join("data", name))


def main():

    # Example playlist
    URI = "spotify:playlist:5CF6KvWn85N6DoWufOjP5T"
    testlength = None

    all_streams = get_history()
    podcasts = get_pods(all_streams)
    music_streams_no_features = remove_pods(all_streams)
    music_streams = add_features(music_streams_no_features, length=testlength)
    playlist_example = add_features(get_playlist(URI), length=testlength, playlist=True)
    no_skip_df = music_streams.query("(playtime_s / duration) > 0.75").reset_index(
        drop=True
    )
    wheel_df = open_wheel()

    df_to_json(podcasts, name="podcasts.json")
    df_to_json(all_streams, name="all_streams.json")
    df_to_json(music_streams_no_features, name="music_streams_no_features.json")
    df_to_json(music_streams, name="music_streams.json")
    df_to_json(no_skip_df, name="no_skip_df.json")
    df_to_json(playlist_example, name="playlist_example.json")
    df_to_json(wheel_df, name="wheel_df.json")


if __name__ == "__main__":
    main()
