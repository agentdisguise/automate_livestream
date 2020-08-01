# automate_livestream
Automatic livestream creator.

Need to:
- create client_secrets,json from Google Developer's Console
- edit lesson.txt in format ```term,subject,day,24 hr time,teacher```
- create a webhook to send slack messages 
  
Command to run:
``` pip install --upgrade google-api-python-client```

Python modules used 
- google_auth_oauthlib
- googleapiclient
- httplib2