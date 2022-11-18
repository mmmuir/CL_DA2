# Getting Started

1: First, ensure [Python 3.10.0](https://www.python.org/downloads/release/python-3100/) is installed on your machine.
If you are unable to install 3.10.0, 3.9.10+ should work, but compatibility is not guaranteed.

2: From your bash terminal (Linux/macOS) or Git Bash (Windows), clone the repository:

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
