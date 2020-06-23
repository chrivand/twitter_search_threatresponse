[![published](https://static.production.devnetcloud.com/codeexchange/assets/images/devnet-published.svg)](https://developer.cisco.com/codeexchange/github/repo/chrivand/twitter_search_threatresponse)

# Twitter Search to Cisco Threat Response Casebook [v1.0]

This is a sample script to search the Twitter hashtag #opendir for threat/malware related observables, check for Target Sightings and automatically add observables to Cisco Casebook. This enables Security Researchers and Threat Responders in a SOC to quickly see if the observables from #opendir have been seen in their environment (by leveraging Cisco Threat Response (CTR)). The #opendir hashtag is used by many threat intelligence researchers to post their findings on new threats.

* For more information on how to use CTR, please review this link: [https://visibility.amp.cisco.com/#/help/introduction](https://visibility.amp.cisco.com/#/help/introduction).

## Known issues
* No known issues. 

## Release notes version 1.0
1. The "twitter" library is being used to reach the [Twitter standard search API](https://developer.twitter.com/en/docs/tweets/search/api-reference/get-search-tweets).
2. The "webexteamssdk" library is beinbg used to post send alerts.
3. The script also removes all clean observables from the case to stop false positives. Often legitimate websites are added in a tweet, but are not an observable associated directly with the malware campaign. This causes Target Sightings, without them being of much interest. Removing these from the investigation is also better for the performance of the script. 
4. The script now also checks for Target Sightings. If there is a Sighting of a Target, the Webex Teams message and the Case description in Casebook will get a "HIGH PRIORITY" tag.

## Overview
1. The script leverages the #opendir Twitter hashtag to find tweets related to new malware campaigns.
2. It will then check if this is the first time the script has run:
   * If the script is being run for the first time, it will parse through all most recent tweets (maximum 100, which usually goes back 3-5 days).
   * If the script has run before, it will check if there are new tweets in #opndir (using the “since_id” element from the Twitter standard search API).
     * If there was an update -> parse all the new tweets.
     * If there was no update -> do nothing.
3.	During the parsing of the tweets, the CTR API is used to retrieve all the observables (using the Inspect API endpoint).
4.  It then removes observables with a clean disposition (retrieved from CTR API).
5.  It also checks for Target Sightings. If there is a Sighting of a Target, the Webex Teams message and the Case description in Casebook will get a "HIGH PRIOIRTY" tag.
5. The last step is to create a CTR Casebook with the retrieved observables. The username and the text of the tweet will be added into the Case. Optionally, a Webex Teams message is sent to a room to update the Threat Responder.


## Installation
1. Clone this repository or download the ZIP file.
2. Log in to [https://visibility.amp.cisco.com/](https://visibility.amp.cisco.com/) with your Cisco Security credentials.
3. Make sure that you have Casebook enabled (+ the Casebook AMP, Threat Grid and Chrome widget, for extended functionality). Please find more information here: [https://visibility.amp.cisco.com/#/help/casebooks](https://visibility.amp.cisco.com/#/help/casebooks).
4. Click on **Modules**.
5. Click on **API Clients**.
6. Click on **Add API Credentials**.
7. Give the API Credentials a name (e.g., *Twitter #opendir parser*).
8. Select at least the **Casebook** and **Private Intelligence** checkboxes; however, to be sure, you can also click **Select All**.
9. Add an optional description if needed.
10. Click on **Add New Client**.
11. The **Client ID** and **Client Secret** are now shown to you. Do NOT click on **close** until you have copy-pasted these credentials to the config.json file in the repository.
12. It is possible to integrate the script with Webex Teams. In order to do that, an API Access Token and a Room ID need to be entered in the config.json file. Please retrieve your key from: [https://developer.webex.com/docs/api/getting-started](https://developer.webex.com/docs/api/getting-started). Then create a dedicated Webex Teams space for these notifications and retrieve the Room ID from: [https://developer.webex.com/docs/api/v1/rooms/list-rooms](https://developer.webex.com/docs/api/v1/rooms/list-rooms). Please be aware that the personal token from the getting started page only works for 12 hours. Please follow these steps to request a token per request: [https://developer.webex.com/docs/integrations](https://developer.webex.com/docs/integrations). This is roadmapped for v3.0 of the script.
13. Make sure you apply for a [Twitter developer account](https://developer.twitter.com/en/apply-for-access). After you have been accepted, you can [create a Twitter app](https://developer.twitter.com/en/apps/create), which creates the right credentials to perform API queries. 
14. Make sure that the config.json file looks like this (with the right keys and IDs filled in between the quotes):

  ```
  {
    "ctr": {
        "client_id": "<client-id-here>",
        "client_password": "<client-password-here>"
    },
    "webex": {
        "access_token": "<access-token-here",
        "room_id": "<room-id-here>"
    },
    "twitter": {
        "token": "<token-here>",
        "token_secret": "<token-secret-here>",
        "consumer_key": "<consumer-key-here>",
        "consumer_secret": "<consumer-secret-here",
        "since_id": 0
    }
}
  ```
  
14.  You are now ready to execute the script. Go to a terminal and change directory to the folder that contains your **twitter_search.py** and **config.json** file. 
15. Make sure you have the correct libraries installed by executing the **requirements.txt** file (using a Python virtual environment!): 

  ```
  python3.6 -m venv twitter_venv
  source twitter_venv/bin/activate
  pip install -r requirements.txt
  ```
  
16. Now execute the **twitter_search.py** script:

  ```
  python3.6 twitter_search.py
  ```

17. You are now done. 

## Notes and Road Map
* Please feel free to use **crontab** to run the script every day. The script will handle this and create a new casebook only if a new blog is added. There is detailed information on how to use crontab here: [https://pypi.org/project/python-crontab/](https://pypi.org/project/python-crontab/). 
* Otherwise, you can also use a function I previously wrote, which is the **intervalScheduler** function in this script: [https://github.com/chrivand/Firepower_O365_Feed_Parser/blob/VERSION-3.0/O365WebServiceParser.py](https://github.com/chrivand/Firepower_O365_Feed_Parser/blob/VERSION-3.0/O365WebServiceParser.py). 
* Technically this script can work with any hashtag, please change it on line 226 of twitter_search.py. In newer versions, I will add the possibility the scan multiple hashtags. 
* I will keep updating this script and you can also do a pull request with an update.
* Please open an "Issue" if there is something not working or if you have a feature request.
* Currently the Webex Teams Authentication works with a temporary token. This will be improved with an official Webex Teams Integration (roadmapped for v2.0).

