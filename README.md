# IG-Downloader
Bulk download Instagram stories

This script will download stories of followed users posted in the past 24 hours. A logged in Instagram account is required to use this.

# Usage
    python3 main.py

On first run, a config file will be generated. The script will ask for some web browser cookie values of a currently logged in user, which can be obtained from the developer tools of Google Chrome or Firefox.

Note that the cookies may need to be periodically refreshed at least every 3 months or else this script may not be able to sucessfully authenticate. 

To periodically obtain stories from followed users, run this script at least every 24 hours. A Windows Scheduled Task or a Unix cron job is recommended to perform this automatically.

# Special Thanks
- https://github.com/CaliAlec/ChromeIGStory
- https://github.com/mgp25/Instagram-API

# License
MIT

# Legal Disclaimer
This project is in no way affiliated with, authorized, maintained, sponsored or endorsed by Instagram or any of its affiliates or subsidiaries. This is an independent project that utilizes Instagram's unofficial API. Use at your own risk.
