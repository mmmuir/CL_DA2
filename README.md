# Getting Started

1: First, ensure [Python 3.10.0](https://www.python.org/downloads/release/python-3100/) is installed on your machine.
If you are unable to install 3.10.0, 3.9.10+ should work, but compatibility is not guaranteed.

2: From your Bash terminal (Linux/macOS) or [Git Bash](https://appuals.com/what-is-git-bash/) (Windows), clone the repository:

`git clone https://github.com/mmmuir/cl_da2.git`

3: After cloning the repo, move into its directory, and initialize a virtual environment using Python's built-in `venv`, e.g.:

`cd cl_da2_clone`
`python -m venv venv_sp`

4: Then install the project requirements from `requirements.txt`, passing `--use-pep517` due to an issue with `ratelimit`'s dependencies. 

`pip install --use-pep517 -r requirements.txt`

5: If using your own [**extended** streaming history](https://support.spotify.com/us/article/understanding-my-data/), empty the contents of the `data` folder, replacing them with your own files. Move only `endsong*.json` files to the folder; for now, this project does not handle short-term streaming history or user libraries. Note that the structure of the JSON provided by Spotify is subject to change; please submit an issue if this occurs, and I will create a branch that parses the files accordingly. Currently, the project supports the JSON structure below:
```
[{
"ts": "YYY-MM-DD 13:30:30",
"username": "_________",
"platform": "_________",
"ms_played": _________,
"conn_country": "_________",s
"ip_addr_decrypted": "___.___.___.___",
"user_agent_decrypted": "_________",
"master_metadata_track_name": "_________,
“master_metadata_album_artist_name:_________”,
“master_metadata_album_album_name:_________",
“spotify_track_uri:_________”,
"episode_name": _________,
"episode_show_name": _________,
“spotify_episode_uri:_________”,
"reason_start": "_________",
"reason_end": "_________",
"shuffle": null/true/false,
"skipped": null/true/false,
"offline": null/true/false,
"offline_timestamp": _________,
"incognito_mode": null/true/false,
}]
```

6: If using your own data, I recommend running `python remove_identifier.py` before proceeding, unless you intend to perform analyses which depend on the data present in those columns, e.g. queries attempting to distinguish home vs. public listening on the basis of IP address / platform. Try `grep '\"ip\_addr\_decrypted\"\:*\"' ./data/endsong*.json` in Bash/Git Bash ensure personal identifiers were properly scrubbed; more robust tests are on the roadmap.

# main_data.py

This file serves as the primary data wrangler, as well as a module containing functions used by `analysis.ipynb`. First, it instantiates class `spotipy.
Spotify`, allowing the program to make API calls. **A demo secret key was provided with the project submission form; if it was not forwarded to you, please contact... whoever is in charge of that, and/or check the `git log` of this repository to find my e-mail address.** 

### To run:

7: Replace `"secret_key_here"` with the demo secret key -- or your own key generated from the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications) using a free Spotify account -- in order to run API calls. See [Spotify Web API Tutorial](https://developer.spotify.com/documentation/web-api/quick-start/) and [Spotipy - Client Credentials Flow](https://spotipy.readthedocs.io/en/master/#client-credentials-flow) for further information.

8: Enter `python main_data.py` from the terminal. This program generally takes about 2.5 minutes to run, with most of the runtime being taken up by API calls. If you receive an error, try adjusting the parameters in the `@limits(calls=150, period=30)` decorator above `add_features()`. If you are unable to run the program due to rate limiting, I have included the resultant DataFrames in JSON format, and you may proceed to run notebook.

### Explanation:
`get_history()` converts locally stored extended streaming history files into a DataFrame, dropping columns scrubbed by `remove_identifier.py` and renaming others for clarity. It also converts `ms_played` to seconds, adds columns for minutes / hours played, and converts each track's timestamp into a timezone-aware DateTime64 format.

`get_pods()` extracts podcasts from the previous DataFrame by selecting all tracks with a null `id` column, which was previously a music-specific `spotify_track_uri` column. 

`remove_pods()` similarly returns a DataFrame without podcasts by checking for a null `episode` column.

`get_playlist()` creates a DataFrame from a public Spotify playlist using a given playlist URI. You can get the URI for any public playlist by taking the seemingly-random numbers and letters from the end of its URL, i.e. the URI for my hit playlist [wow im at the beach](https://open.spotify.com/playlist/5CF6KvWn85N6DoWufOjP5T) is `5CF6KvWn85N6DoWufOjP5T`. If there is a question-mark in the URL, remove it along with any characters to the right.

`open_wheel()` opens a JSON representation of the [Camelot Wheel](https://mixedinkey.com/camelot-wheel/), a simplified representation of the ["circle of fifths."](https://en.wikipedia.org/wiki/Circle_of_fifths) This portion of the project will be greatly expanded upon in the future. For know, just know that this function, along with `key_to_camelot()` and `get_friendly()`, enable the program to reveal which tracks in a playlist or listening history are most harmonically compatible with a given inputted track.

`add_features()` takes the DataFrame of locally stored streaming history as an input, querying the API to add information such as tempo, key signature, and track duration.

`df_to_json() and json_to_df()` pack and unpack the DataFrames to and from JSON format.

`main()` executes all of the above functions, except for those used in `analysis.ipynb`.

# analysis.ipynb

### To run:

Open in Jupyter or a .ipynb reader in your favorite IDE and press "run all". Be sure to select the ipykernel installed in the venv set up for this project.

## Explanation:

Please see notebook's markdown and comments. This section will be expanded.