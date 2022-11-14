from os import path
import json
from glob import glob


def remove_identifiers():
    history = glob(path.join("data", "endsong_*.json"))
    for i in range(len(history)):
        with open(
            path.join("data", f"endsong_{i}.json"), "r+", encoding="utf-8"
        ) as json_file:
            user_json = json.load(json_file)
            for i in range(len(user_json)):
                user_json[i].update(
                    {
                        "username": None,
                        "conn_country": None,
                        "ip_addr_decrypted": None,
                        "user_agent_decrypted": None,
                        "platform": None,
                    }
                )
            json_file.seek(0)
            json_file.write(json.dumps(user_json))
            json_file.truncate()


remove_identifiers()
