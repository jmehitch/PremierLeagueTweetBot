#! python3
# PremierLeagueTwitterBot.py - a Twitter Bot that sends out a tweet/tweet thread of today's Premier League fixtures

import http.client
import json
import datetime
import tweepy
import schedule
import time 


### ----- Twitter Authentication -----


def twitter_auth():
    """Authenticates and connects to Twitter API"""
    
    # Twitter API Keys
    consumer_key = "xv2KYZLVCpcduMWajMBtvwtvb"
    consumer_secret_key = "**********"
    access_token = "**********"
    access_token_secret = "**********"

    # Twitter API authorisation
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret_key)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    return api


### ----- Send tweets of today's fixtures -----


def construct_fixtures_tweets():
    """Connects to football-data API and creates fixtures"""

    # Declares today's date
    today = str(datetime.date.today())

    # Gets today's fixtures data from football-data.org API
    connection = http.client.HTTPConnection('api.football-data.org')
    headers = {'X-Auth-Token': '**********'}
    connection.request('GET', '/v2/competitions/PL/matches?dateFrom='+today+'&dateTo='+today, None, headers)
    response = json.loads(connection.getresponse().read().decode())

    # Initialises fixtures tweet
    tweet1 = "Today's #PremierLeague matches:\n"
    tweet2 = ""
    tweet3 = ""

    # Checks if any fixtures on today
    if response['matches']:
        # For each fixture obtained, appends line to tweet with information
        for i in range(len(response['matches'])):
            time = response['matches'][i]['utcDate']
            ko_time = str(datetime.datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ'))[-8:-3]
            tweet_line = response['matches'][i]['homeTeam']['name'] + ' vs ' + response['matches'][i]['awayTeam'][
                'name'] + ' (' + ko_time + ')' + '\n'
            # Checks that tweet will not be too long (~ >280 chars), by splitting into separate tweets
            if len(tweet1) >= 220:
                tweet2 += tweet_line
            elif len(tweet2) >= 220:
                tweet3 += tweet_line
            else:
                tweet1 += tweet_line
        return send_fixtures_tweets(tweet1, tweet2, tweet3)
    else:
        return print('No PL fixtures today')


def send_fixtures_tweets(tweet1, tweet2, tweet3):
    """Publishes tweets to timeline using Twitter API"""

    # Authorises Twitter API connection
    api = twitter_auth()

    # Checks if tweet has already been made today
    get_tweet = api.user_timeline(count=1,tweet_mode="extended")
    last_tweet = get_tweet[0].full_text
    tweet = tweet1[:-1]
    if last_tweet == tweet:
        return print('Tweet already sent')
        
    # Sends tweets to timeline, depending on how many tweets created
    # Multiple tweets sent as a thread by responding to previous tweet
    if tweet3:
        first_tweet = api.update_status(tweet1)
        first_id = first_tweet.id
        second_tweet = api.update_status(tweet2, first_id)
        second_id = second_tweet.id
        api.update_status(tweet3, second_id)
        return print('Successfully sent tweet(s)')
    elif tweet2:
        first_tweet = api.update_status(tweet1)
        first_id = first_tweet.id
        api.update_status(tweet2, first_id)
        return print('Successfully sent tweet(s)')
    else:
        api.update_status(tweet1)
        return print('Successfully sent tweet(s)')


### ----- Reply to tweets (player goals) -----


def get_last_replied_id(file):
    """Retreives last replied tweet ID from txt file"""
    f = open(file, 'r')
    last_replied_id = int(f.read().strip())
    f.close()
    return last_replied_id


def store_last_replied_id(last_replied_id, file):
    """Stores last replied tweet ID in txt file"""
    f = open(file, 'w')
    f.write(str(last_replied_id))
    f.close()
    return


def reply_goals_tweets():
    """Replies to users who have tweeted the bot a player's name, stating no of goals scored"""

    # Authorise Twitter API connection
    api = twitter_auth()

    # Get last mention
    mentions = api.mentions_timeline()

    # Tweet to reply to
    tweet_id = mentions[0].id
    reply_to = "@"+mentions[0].user.screen_name

    # Check if already replied to last mention
    last_tweet_id = int(get_last_replied_id("last_replied_id.txt"))

    if last_tweet_id == tweet_id:
        return print("Already replied to query")

    # Get player name from tweet
    player = mentions[0].text[12:].lower()

    # Gets today's fixtures data from football-data.org API
    connection = http.client.HTTPConnection('api.football-data.org')
    headers = {'X-Auth-Token': '**********'}
    connection.request('GET', '/v2/competitions/PL/scorers?limit=400', None, headers)
    response = json.loads(connection.getresponse().read().decode())

    # Loop through all PL scorers and search for match
    for i in response['scorers']:
        # TODO - REMOVE ACCENTS
        # If player matches scored DB send tweet stating goals scored
        if i['player']['name'].lower() == player:
            goals_scored = str(i['numberOfGoals'])
            tweet_str = reply_to + " " + player.title() + " has scored " + goals_scored + \
                " goals this season #PremierLeagueStats"
            store_last_replied_id(tweet_id, "last_replied_id.txt")
            api.update_status(tweet_str, in_reply_to_status_id=tweet_id)
            return print('Bot replied to '+reply_to)
    # If player not found or hasn't scored reply stating this
    tweet_str = reply_to + " Player not scored (or name not spelt correctly)"
    store_last_replied_id(tweet_id, "last_replied_id.txt")
    api.update_status(tweet_str, in_reply_to_status_id=tweet_id)
    return print('no player found from '+reply_to+"'s tweet")


def main():
    # Runs fixtures script at 11:00AM every day
    schedule.every().day.at("11:00").do(construct_fixtures_tweets)

    while True: 
        schedule.run_pending()
        # Runs reply with goals script every 30s 
        reply_goals_tweets()
        time.sleep(30) # Wait 30 secs
        # Print run status to log
        print('still running at '+ str(datetime.datetime.time(datetime.datetime.now()))[:5])


if __name__ == "__main__":
    main()
