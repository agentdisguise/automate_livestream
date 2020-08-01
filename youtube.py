import httplib2
import os
import sys
import datetime
import json

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google.oauth2.credentials
import google_auth_oauthlib.flow
from google_auth_oauthlib.flow import InstalledAppFlow
import google.auth.transport.requests

# Bc GMT sucks 
AEST_MODIFIER = -10

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the {{ Google Cloud Console }} at
# {{ https://cloud.google.com/console }}.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
CLIENT_SECRETS_FILE = "client_secrets.json"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account.
SCOPES = "https://www.googleapis.com/auth/youtube"
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

# This variable defines a message to display if the CLIENT_SECRETS_FILE is
# missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0
To make this sample run you will need to populate the client_secrets.json file
found at:
   %s
with information from the {{ Cloud Console }}
{{ https://cloud.google.com/console }}
For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))

def get_authenticated_service():
    try: 
        with open('tokens.json') as data_file:
            temp = json.load(data_file)
    except:        
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
        authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
        # This asks for the authorisation code
        credentials = flow.run_console()

        # Save the credentials to a json file so we can use it again later
        save_credentials(credentials)
    else:
        # We have some credentials saved so load it
        credentials = google.oauth2.credentials.Credentials(
            temp['token'],
            refresh_token=temp['refresh_token'],
            id_token=temp['id_token'],
            token_uri=temp['token_uri'],
            client_id=temp['client_id'],
            client_secret=temp['client_secret'],
            scopes=[SCOPES],
        )
        expiry = temp['expiry']
        expiry_datetime = datetime.datetime.strptime(expiry,'%Y-%m-%d %H:%M:%S')
        credentials.expiry = expiry_datetime

        # Refresh the token if it's expired 
        if expiry_datetime < datetime.datetime.now():
            request = google.auth.transport.requests.Request()
            if credentials.expired:
                new_creds = credentials.refresh(request)
                # Update the refresh token and time 
                save_credentials(credentials)


    return build(API_SERVICE_NAME, API_VERSION, credentials = credentials)

def save_credentials(credentials):
    temp = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'id_token':credentials.id_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes,
        'expiry':datetime.datetime.strftime(credentials.expiry,'%Y-%m-%d %H:%M:%S')
    }
    
    with open('tokens.json', 'w', encoding='utf-8') as f:
        json.dump(temp, f, ensure_ascii=False, indent=4)


# Create a liveBroadcast resource and set its title, scheduled start time,
# scheduled end time, and privacy status.
def insert_broadcast(youtube, options):
    aest_time = options.classtime + datetime.timedelta(hours=AEST_MODIFIER)
    insert_broadcast_response = youtube.liveBroadcasts().insert(
        part="snippet,status,contentDetails",
        body=dict(
            snippet=dict(
                title=str(options),
                scheduledStartTime=aest_time.isoformat(),
            ),
            status=dict(
                privacyStatus="unlisted",
                selfDeclaredMadeForKids=False
            ),
            contentDetails=dict(
                latencyPreference="ultraLow"
            )
        )
    ).execute()

    snippet = insert_broadcast_response["snippet"]

    print ("Broadcast '%s' with title '%s' was published at '%s'." % (
           insert_broadcast_response["id"], snippet["title"], snippet["publishedAt"]))
    return insert_broadcast_response["id"]

def update_broadcast(broadcast_id, youtube, options):   
    update_broadcast_response = youtube.videos().update(
        part='id,snippet,status',
        body=dict(
            id=broadcast_id,
            snippet=dict(
                title=str(options),
                categoryId="27",
                description="hello"
            ),
            status=dict(
                selfDeclaredMadeForKids=False
            )
        )
    ).execute()

    print("Broadcast was updated.")

# Create a liveStream resource and set its title, format, and ingestion type.
# This resource describes the content that you are transmitting to YouTube.
def insert_stream(youtube, options):
    insert_stream_response = youtube.liveStreams().insert(
        part="snippet,cdn",
        body=dict(
            snippet=dict(
                title=str(options),
                description="Education"
            ),
            cdn=dict(
                format="variable",
                ingestionType="rtmp"
            )
        )
    ).execute()

    snippet = insert_stream_response["snippet"]
    cdn = insert_stream_response["cdn"]

    print ("Stream '%s' with title '%s' was inserted." % (
           insert_stream_response["id"], snippet["title"]))
    return (insert_stream_response["id"], cdn["ingestionInfo"]["streamName"])

# Bind the broadcast to the video stream. By doing so, you link the video that
# you will transmit to YouTube to the broadcast that the video is for.
def bind_broadcast(youtube, broadcast_id, stream_id):
    bind_broadcast_response = youtube.liveBroadcasts().bind(
        part="id,contentDetails",
        id=broadcast_id,
        streamId=stream_id
    ).execute()

    print ("Broadcast '%s' was bound to stream '%s'." % (
           bind_broadcast_response["id"],
           bind_broadcast_response["contentDetails"]["boundStreamId"]))