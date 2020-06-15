from twitter import *
import json
from threatresponse import ThreatResponse
from datetime import datetime
import os
import webexteamssdk


def open_config():
    '''
    this function opens config.json
    '''
    if os.path.isfile("config.json"):
        global config_file
        with open("config.json", 'r') as config_file:
            config_file = json.loads(config_file.read())
            print("\nThe config.json file was loaded.\n")
    else:
        print("No config.json file, please make sure config.json file is in same directory.\n")



def write_config():
    ''' 
    This function writes to config.json
    '''
    with open("config.json", 'w') as output_file:
        json.dump(config_file, output_file, indent=4)



def return_observables(tweet_text):
    '''
    this function will parse raw text and return the observables and types
    '''
    ctr_client = ThreatResponse(
    client_id=config_file["ctr"]["client_id"],  
    client_password=config_file["ctr"]["client_password"],  
    region='us',  # can be change to eu or apjc
    )

    data = {"content":tweet_text}

    response = ctr_client.inspect.inspect(data)

    #check if request was succesful
    if response:
        return(response) 
    else:
        print(f"Observable parsing request failed, status code: {response.status_code}\n")



def return_non_clean_observables(returned_observables_json):
    '''
    this function returns only non clean observables (to remove noise)
    '''

    ctr_client = ThreatResponse(
    client_id=config_file["ctr"]["client_id"],  
    client_password=config_file["ctr"]["client_password"],  
    region='us',  # can be change to eu or apjc
    )

    # create empty list to store clean observables
    clean_observables = []
    
    # retrieve dispositions for observables
    response = ctr_client.enrich.deliberate.observables(returned_observables_json)

    disposition_observables = response

    # parse through json and search for observables with clean disposition (1)
    for module in disposition_observables['data']:
        module_name = module['module']
        if 'verdicts' in module['data'] and module['data']['verdicts']['count'] > 0:
            docs = module['data']['verdicts']['docs']
            for doc in docs:
                observable = doc['observable']
                # if the disposition is clean / 1 then add to separate list to remove from other list
                if doc['disposition'] == 1:
                    clean_observables.append(observable)
                    #print(f"Clean observable, omitting: {observable}\n")

    non_clean_observables = [i for i in returned_observables_json if not i in clean_observables or clean_observables.remove(i)]
    
    non_clean_observables_json = non_clean_observables

    return non_clean_observables_json



def check_for_sighting(returned_observables_json):
    '''
    this function checks if there is a sighting for a specific observable
    '''
    ctr_client = ThreatResponse(
    client_id=config_file["ctr"]["client_id"],  
    client_password=config_file["ctr"]["client_password"],  
    region='us',  # can be change to eu or apjc
    )

    data = returned_observables_json

    response = ctr_client.enrich.observe.observables(data)
    
    #check if request was succesful
    if response:
        
        returned_data = response

        total_amp_sighting_count = 0
        total_umbrella_sighting_count = 0
        total_email_sighting_count = 0

        # run through all modules to check for sightings (currently checking the amp, umbrella and SMA modules)
        for module in returned_data['data']:
            if module['module'] == "AMP for Endpoints":
                # json key not always there, error checking...
                if 'sightings' in module['data']:
                    # store amount of sightings
                    total_amp_sighting_count = module['data']['sightings']['count']

            if module['module'] == "Umbrella":
                # json key not always there, error checking...
                if 'sightings' in module['data']:
                    # store amount of sightings
                    total_umbrella_sighting_count = module['data']['sightings']['count']

            if module['module'] == "SMA Email":
                # json key not always there, error checking...
                if 'sightings' in module['data']:
                    # store amount of sightings
                    total_email_sighting_count = module['data']['sightings']['count']

        # create dict to store information regarding the sightings

        total_sighting_count = total_amp_sighting_count + total_umbrella_sighting_count + total_email_sighting_count

        return_sightings = {
            'total_sighting_count': total_sighting_count,
            'total_amp_sighting_count': total_amp_sighting_count,
            'total_umbrella_sighting_count': total_umbrella_sighting_count,
            'total_email_sighting_count': total_email_sighting_count
        }

        return(return_sightings)

    else:
        print(f"Sighting check request failed, status code: {response.status_code}\n")
        return(response.status_code)



def new_casebook(returned_observables_json,returned_sightings,user_name,tweet_text):
    '''
    this function post list of observables to new case in casebook
    '''
    ctr_client = ThreatResponse(
    client_id=config_file["ctr"]["client_id"],  
    client_password=config_file["ctr"]["client_password"],  
    region='us',  # can be change to eu or apjc
    )

    # create title and description for SOC researcher to have more context, if there are sightings, add high priority
    if returned_sightings['total_sighting_count'] == 0:
        casebook_title = " #opendir Tweet: " + user_name
    if returned_sightings['total_sighting_count'] != 0:
        casebook_title = "*HIGH PRIORITY* #opendir Tweet: " + user_name

    casebook_description = f"Twitter generated casebook from #opendir by: {user_name}, Tweet: {tweet_text}"
    casebook_datetime = datetime.now().isoformat() + "Z"

    # create right json format to create casebook
    casebook_json = {
        "title": casebook_title,
        "description": casebook_description,
        "observables": returned_observables_json,
        "type": "casebook",
        "timestamp": casebook_datetime   
    }

    # post request to create casebook
    response = ctr_client.private_intel.casebook.post(casebook_json)
    if response:
        print(f"[201] Success, case added to Casebook added from #opendir Tweet by: {user_name}\n")
        
        # if Webex Teams tokens set, then send message to Webex room
        if config_file['webex']['access_token'] is '' or config_file['webex']['room_id'] is '':

            # user feed back
            print("Webex Teams not set.\n\n")
        else:            
            # instantiate the Webex handler with the access token
            teams = webexteamssdk.WebexTeamsAPI(config_file['webex']['access_token'])

            # post a message to the specified Webex room 
            try:
                if returned_sightings['total_sighting_count'] == 0:
                    webex_text = f"New case added to Casebook added from #opendir Tweet by: {user_name}"
                    message = teams.messages.create(config_file['webex']['room_id'], text=webex_text) 
                if returned_sightings['total_sighting_count'] != 0:
                    webex_text = f"New case added to Casebook added from #opendir Tweet by: {user_name}. 🚨🚨🚨  HIGH PRIORITY, Target Sightings have been identified! AMP targets: {str(returned_sightings['total_amp_sighting_count'])}, Umbrella targets: {str(returned_sightings['total_umbrella_sighting_count'])}, Email targets: {str(returned_sightings['total_email_sighting_count'])}. 🚨🚨🚨"
                    message = teams.messages.create(config_file['webex']['room_id'], text=webex_text)
            # error handling, if for example the Webex API key expired
            except Exception:
                print("Webex authentication failed... Please make sure Webex Teams API key has not expired. Please review developer.webex.com for more info.\n")
    else:
        print(f"Something went wrong while posting the casebook to CTR, status code: {response.status_code}\n")

    return response



def twitter_search():
    '''
    This function will retrieve the most recent tweets with the #opendir hashtag.
    It will not return tweets that have been previously returned (using the since_id)
    '''

    twitter_client = Twitter(
    auth=OAuth(config_file["twitter"]["token"], config_file["twitter"]["token_secret"], config_file["twitter"]["consumer_key"], config_file["twitter"]["consumer_secret"]))


    # Search for the latest tweets about #opendir
    results = twitter_client.search.tweets(q="#opendir", count=100, result_type="recent", since_id=config_file["twitter"]["since_id"])

    if results['statuses']:
        config_file['twitter']['since_id'] = results['statuses'][0]['id']
        write_config()

        #loop through tweets
        for tweet in results['statuses']:
            #user feedback
            print(f"New tweet detected! ID: {tweet['id']}, Date: {tweet['created_at']}.\n\n")

            # username + text from tweet
            user_name = tweet['user']['name']
            tweet_text = tweet['text']

            # retrieve observables from text
            returned_observables_json = return_observables(tweet_text)

            # return non clean (malicious, unkown etc.) observables only
            non_clean_observables_json = return_non_clean_observables(returned_observables_json) 

            # if observables were returned (list not empty), create a casebook
            if non_clean_observables_json != "[]":      
                
                # retrieve target sightings for observables
                returned_sightings = check_for_sighting(non_clean_observables_json)

                # create new case in casebook
                new_casebook(non_clean_observables_json,returned_sightings,user_name,tweet_text)
            else:
                print(f"No new case created in casebook (no observables found) from: {entry_title}\n")

    else:
        # no changes since last since_id
        print(f"No changes to #opendir detected, please try again later. Recommendation is to schedule the script daily (or 2-3 times a day).\n")

            

### main script 
if __name__ == "__main__":
    try:
        # open config json file and grab client_id and secret
        open_config()
     
        # main function: retrieve twitter results, parse, investigate and create casebook
        twitter_search()


    except KeyboardInterrupt:
        print("\nExiting...\n")
