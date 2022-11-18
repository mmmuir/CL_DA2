# Getting Started

1: First, ensure [Python 3.10.0](https://www.python.org/downloads/release/python-3100/) is installed on your machine.
If you are unable to install 3.10.0, 3.9.10+ should work, but compatibility is not guaranteed.

2: From your Bash terminal (Linux/macOS) or [Git Bash](https://appuals.com/what-is-git-bash/) (Windows), clone the repository:

`git clone https://github.com/mmmuir/cl_da2_clone`

3: After cloning the repo, move into its directory, and initialize a virtual environment using Python's built-in `venv`, e.g.:

`cd cl_da2_clone`
`python -m venv venv_sp`

4: Then install the project requirements from `requirements.txt`. 

`pip install -r requirements.txt`

5: If using your own [**extended** streaming history](https://support.spotify.com/us/article/understanding-my-data/), empty the contents of the `data` folder, replacing them with your own files. Move only `endsong*.json` files to the folder; for now, this project does not handle short-term streaming history or user libraries. Note that the structure of the JSON provided by Spotify is subject to change; please submit an issue if this occurs, and I will create a branch that parses the files accordingly. Currently, the project supports the JSON structure below:
```[{
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

# `main_data.py`

This file serves as the primary data wrangler, as well as a module containing functions used by `analysis.ipynb`. First, it instantiates an instance of `spotipy.Spotify`, allowing the program to make API calls. **A demo secret key was provided with the project submission form; if it was not forwarded to you, please contact... whoever is in charge of that, and/or check the `git log` of this repository to find my e-mail address.