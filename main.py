import json
import logging
import sys
import time
import os
import instagram
import tarfile

def saveJSON(timestamp: int, type: str, content: dict):
    """Save JSON file

    Args:
        timestamp: Unix timestamp
        type: Name
        content: JSON data

    Returns:
        None
    """
    dirpath = os.getcwd()
    path = os.path.join(dirpath, "json", str(timestamp) + "_" + type + ".json")
    dirpath = os.path.dirname(path)
    os.makedirs(dirpath, exist_ok=True)
    f = open(path, "tx")
    json.dump(content, f)
    f.close()

def main():
    """ Main function

    Returns:
        None
    """
    configfile = "config.json"
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

    try:
        logging.info("Opening config file.")
        f = open(configfile, "tr")
    except FileNotFoundError:
        logging.info("File not found.")
        logging.info("Creating new config file.")
        f = open(configfile, "tx+")

    try:
        logging.info("Loading config file.")
        config = json.load(f)
    except json.decoder.JSONDecodeError:
        logging.info("Config file corrupted.")
        logging.info("Creating new config file.")
        f.close()
        f = open(configfile, "tw+")
        logging.info("Updating config.")
        iguserid = input("Enter your IG user ID: ")
        igsessionid = input("Enter your IG session ID: ")
        igcsrftoken = input("Enter your IG CSRF token: ")
        igmid = input("Enter your IG mid: ")
        config = {
            "ds_user_id": iguserid,
            "sessionid" : igsessionid,
            "csrftoken" : igcsrftoken,
            "mid" : igmid,
        }
        logging.info("Saving config.")
        json.dump(config, f) # Save config

    #logging.info("Config settings:")
    #logging.info("%s", config) # Contains private data
    f.close()

    # Insert error checking to see if config is valid and works

    logging.info("Initialize IG interface.")
    ig = instagram.instagram(config)
    logging.info("Get story tray.")
    traytime = int(time.time())
    storyresp = ig.getStories()
    storyjson = storyresp.json()
    saveJSON(traytime, "tray", storyjson)

    logging.info("Downloading story tray.")
    ig.downloadTray(storyjson)
    users = ig.getUserIDs(storyjson)
    for user in users:
        reeltime = int(time.time())
        uresp = ig.getUserStories(user)
        ujson = uresp.json()
        saveJSON(reeltime, "reel_" + str(user), ujson)
        ig.downloadReel(ujson)

    logging.info("Downloading post-live stories.")
    ig.downloadStoryLive(storyjson)

    logging.info("Collecting list of JSON objects.")
    jsonlist = []
    for file in os.listdir("json"):
        if file.endswith(".json"):
            jsonlist.append(os.path.join("json", file))

    logging.info("Creating tar.xz file of JSON objects.")
    path = os.path.join(os.getcwd(), "json", str(traytime) + ".tar.xz")
    tar = tarfile.open(path, "x:xz")
    for path in jsonlist:
        tar.add(path)
    tar.close()

    logging.info("Removing old JSON objects.")
    for path in jsonlist:
        os.remove(path)

    logging.info("Done.")

if __name__ == "__main__":
    main()
