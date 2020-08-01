import datetime
import math
import youtube
import json
import os
import httplib2
from googleapiclient.errors import HttpError

# Global variables yay
term_start = datetime.datetime.strptime("2020-7-20", "%Y-%m-%d").date()

days = {
    0 : "Monday",
    1 : "Tuesday",
    2 : "Wednesday",
    3 : "Thursday",
    4 : "Friday",
    5 : "Saturday",
    6 : "Sunday"
}

class Lesson():
    def __init__(self, term, week, subject, day, classtime, teacher):
        self._term      = term
        self._week      = week
        self._subject   = subject
        self._day       = day
        self._classtime = classtime
        self._teacher   = teacher
    
    @property
    def classtime(self):
        return self._classtime

    def slack_string(self):
        print_time = self._classtime.strftime("%I:%M%p")
        return f'{self._subject} {print_time} {self._teacher}'

    # Function to format livestream name 
    def __str__(self):
        print_time = self._classtime.strftime("%I:%M%p")
        output = f'T{self._term} | Week {self._week} | {self._subject} {self._day} {print_time} {self._teacher}'
        return output

# Send message to slack
def slack_message(lesson, stream_key, broadcast_id):

    string = lesson.slack_string() + "\n" + stream_key + "\n" + "youtube.com/watch?v=" + broadcast_id

    url = 'slack webhook url'
    bot_message = {
        'text' : string
    }

    message_headers = {'Content-Type': 'application/json; charset=UTF-8'}

    http_obj = httplib2.Http()

    response = http_obj.request(
        uri=url,
        method='POST',
        headers=message_headers,
        body=json.dumps(bot_message),
    )

    print("Message sent\n")

# Youtube authentication yay
youtube_auth = youtube.get_authenticated_service()

# Grab the date and figure out what day and week it is
to_day = datetime.date.today()
week_day = days.get(to_day.weekday())
week_num = math.ceil((to_day - term_start).days / 7) 

# Search through lesson.txt for lessons that are on and save the information to a class
with open("lesson.txt", "r") as f:
    for line in f:
        if week_day in line: 
            term, subject, day, classtime, teacher = line.split(',')

            # Converting the class time to a datetime object 
            hour, minute = map(int , classtime.split(':'))
            classtime = datetime.time(hour, minute, 0)
            classtime = datetime.datetime.combine(datetime.date.today(), classtime)

            lesson = Lesson(term, week_num, subject, day, classtime, teacher)
            print(lesson)

            # Do the youtube things
            try:
                broadcast_id = youtube.insert_broadcast(youtube_auth, lesson)
                youtube.update_broadcast(broadcast_id, youtube_auth, lesson)
                (stream_id, stream_key) = youtube.insert_stream(youtube_auth, lesson)
                youtube.bind_broadcast(youtube_auth, broadcast_id, stream_id)
            except HttpError as e:
                print (f"An HTTP error {e.resp.status} occurred:\n {e.content}")
            
            slack_message(lesson, stream_key, broadcast_id)