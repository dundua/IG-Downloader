import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import logging
import os
from datetime import datetime
try:
    import defusedxml.minidom as xml
except ImportError:
    import xml.dom.minidom as xml

class instagram:
    def __init__(self, cookie):
        """This sets up this class to communicate with Instagram.

        Args:
            cookie: A dictionary object with the required cookie values (ds_user_id, sessionid, csrftoken).
        """
        self.userid = cookie["ds_user_id"]
        self.sessionid = cookie["sessionid"]
        self.csrftoken = cookie["csrftoken"]
        self.mid = cookie["mid"]
        self.headers = {
            "accept"           : "*/*",
            "accept-encoding"  : "gzip, deflate",
            "accept-language"  : "en-US",
            "content_type"     : "application/x-www-form-urlencoded; charset=UTF-8",
            "cache-control"    : "no-cache",
            "cookie"           : "ds_user_id=" + self.userid + "; sessionid=" + self.sessionid + "; csrftoken=" + self.csrftoken + "; mid=" + self.mid,
            "dnt"              : "1",
            # "pragma" : "no-cache",
            # "referer" : "https://www.instagram.com/",
            "user-agent"       : "Instagram 10.26.0 (iPhone7,2; iOS 10_1_1; en_US; en-US; scale=2.00; gamut=normal; 750x1334) AppleWebKit/420+",
            "x-ig-capabilities": "36oD",
            # "x-ig-connection-type" : "WIFI",
            # "x-ig-fb-http-engine" : "Liger"
        }
        self.session = requests.Session()
        max_tries = 3
        backoff_factor = 0.2
        status_forcelist = (500, 502, 503, 504)
        retry = Retry(total=max_tries, read=max_tries, connect=max_tries, backoff_factor=backoff_factor, status_forcelist=status_forcelist)
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.session.headers = self.headers

    def getReelTray(self):
        """Get reel tray from API.

        Returns:
            Response object with reel tray API response
        """
        endpoint = "https://i.instagram.com/api/v1/feed/reels_tray/"
        response = self.session.get(endpoint, timeout=60)
        if response.status_code != requests.codes.ok:
            logging.error("Status Code Error." + str(response.status_code))
            response.raise_for_status()
        return response

    def getReelMedia(self, user):
        """Get reel media of a user from API.

        Args:
            user: User ID

        Returns:
            Response object with reel media API response
        """
        endpoint = "https://i.instagram.com/api/v1/feed/user/" + str(user) + "/reel_media/"
        response = self.session.get(endpoint, timeout=60)
        if response.status_code != requests.codes.ok:
            logging.error("Status Code Error." + str(response.status_code))
            response.raise_for_status()
        return response

    def getStories(self):
        return self.getReelTray()

    def getUserStories(self, user):
        return self.getReelMedia(user)

    def getUserIDs(self, json: dict) -> list:
        """Extract user IDs from reel tray JSON.

        Args:
            json: Reel tray response from IG

        Returns:
            List of user IDs
        """
        users = []
        for user in json['tray']:
            users.append(user['user']['pk'])
        return users

    def getFile(self, url: str, dest: str):
        """Download file and save to destination

        Args:
            url: URL of item to download
            dest: File system destination to save item to

        Returns:
            None
        """
        logging.debug("URL: %s", url)
        logging.debug("Dest: %s", dest)
        try:
            if os.path.getsize(dest) == 0:
                logging.info("Empty file exists. Removing.")
                os.remove(dest)
        except FileNotFoundError:
            pass

        try:
            dirpath = os.path.dirname(dest)
            os.makedirs(dirpath, exist_ok=True)
            with open(dest, "xb") as handle:
                response = self.session.get(url, stream=True, timeout=60)
                if response.status_code != requests.codes.ok:
                    logging.error("Status Code Error." + str(response.status_code))
                    response.raise_for_status()
                for data in response.iter_content(chunk_size=4194304):
                    handle.write(data)
                handle.close()
        except FileExistsError:
            logging.info("File already exists.")

        if os.path.getsize(dest) == 0:
            logging.info("Error downloading. Removing.")
            os.remove(dest)

    def formatPath(self, user: str, pk: int, timestamp: int, postid: str, mediatype: int) -> str:
        """Format download path to a specific format/template

        Args:
            user: User name
            pk: User ID
            timestamp: UTC Unix timestamp
            postid: Post ID
            mediatype: Media type as defined by IG

        Returns:
            None
        """
        dirpath = os.path.dirname(__file__)
        utcdatetime = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d-%H-%M-%S")
        if mediatype == 1:
            ext = ".jpg"
            type = "stories"
        elif mediatype == 2:
            ext = ".mp4"
            type = "stories"
        elif mediatype == 3:
            ext = ".mp4"
            type = "livestories"
        else:
            ext = ""
            type = "other"
        path = os.path.join(dirpath, "downloads", user + "_" + str(pk), type, utcdatetime + "_" + str(timestamp) + "_" + postid + ext)
        return path

    def downloadReel(self, resp):
        """Download stories of a followed user's tray.

        Download the stories of a followed user.

        Args:
            resp: JSON dictionary of reel from IG API

        Returns:
            None
        """
        try:
            for index, item in enumerate(resp['items']):
                logging.debug('    ' + str(index))
                username = item['user']['username']
                userpk = item['user']['pk']
                timestamp = item['taken_at']
                postid = item['id']
                mediatype = item['media_type']
                if mediatype == 2: # Video
                    largest = 0
                    for versionindex, video in enumerate(item['video_versions']):
                        itemsize = video['width'] * video['height']
                        largestsize = item['video_versions'][largest]['width'] * \
                                      item['video_versions'][largest]['height']
                        if itemsize > largestsize:
                            largest = versionindex
                    logging.debug('        V' + str(largest))
                    url = item['video_versions'][largest]['url']
                    logging.debug('            ' + url)
                elif mediatype == 1: # Image
                    largest = 0
                    for versionindex, image in enumerate(item['image_versions2']['candidates']):
                        itemsize = image['width'] * image['height']
                        largestsize = item['image_versions2']['candidates'][largest]['width'] * \
                                      item['image_versions2']['candidates'][largest]['height']
                        if itemsize > largestsize:
                            largest = versionindex
                    logging.debug('        I' + str(largest))
                    url = item['image_versions2']['candidates'][largest]['url']
                    logging.debug('            ' + url)
                else: # Unknown
                    logging.debug('        E')
                    url = None
                    pass

                path = self.formatPath(username, userpk, timestamp, postid, mediatype)
                self.getFile(url, path)
        except KeyError: # JSON 'item' key does not exist for later items in tray as of 6/2/2017
            pass

    def downloadTray(self, resp):
        """Download stories of logged in user's tray.

        Download the stories as available in the tray. The tray contains a list of
        reels, a collection of the stories posted by a followed user.

        The tray only contains a small set of reels of the first few users. To download
        the rest, a reel must be obtained for each user in the tray.

        Args:
            resp: JSON dictionary of tray from IG API

        Returns:
            None
        """
        for reel in resp['tray']:
            self.downloadReel(reel)

    def downloadStoryLive(self, resp):
        """Download post-live stories of a followed user's tray.

        Download the post-live stories of a followed user.

        Args:
            resp: JSON dictionary of reel from IG API

        Returns:
            None
        """
        try:
            for index,item in enumerate(resp["post_live"]["post_live_items"]):
                logging.debug('    ' + str(index))
                username = item["user"]["username"]
                userpk = item["user"]["pk"]
                for bindex,broadcast in enumerate(item["broadcasts"]):
                    logging.debug('        ' + str(bindex))
                    timestamp = broadcast["published_time"]
                    postid = broadcast["media_id"]
                    dash = broadcast["dash_manifest"]
                    dashxml = xml.parseString(dash)
                    elements = dashxml.getElementsByTagName("BaseURL")
                    for eindex,element in enumerate(elements):
                        for node in element.childNodes:
                            if node.nodeType == node.TEXT_NODE:
                                url = node.data
                                mediatype = 3
                                path = self.formatPath(username, userpk, timestamp, postid + "_" + str(eindex), mediatype)
                                self.getFile(url, path)
        except KeyError: # No "post_live" key
            logging.debug('    ' + 'No live stories.')

    def close(self):
        """Close seesion to IG

        Returns:
            None
        """
        self.session.close()
