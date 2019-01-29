#! python3
# PremierLeagueTwitterBot.py - a Twitter Bot that sends out a tweet/tweet thread of today's Premier League fixtures

import http.client
import json
import datetime
import tweepy


def twitter_auth():
    """Authenticates and connects to Twitter API"""
    
    # Twitter API Keys
    consumer_key = "*****"
    consumer_secret_key = "*****"
    access_token = "*****"
    access_token_secret = "*****"

    # Twitter API authorisation
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret_key)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    return api


def construct_fixtures_tweets():
    """Connects to football-data API and creates fixtures"""

    # Declares today's date
    today = str(datetime.date.today())

    # Gets today's fixtures data from football-data.org API
    connection = http.client.HTTPConnection('api.football-data.org')
    headers = {'X-Auth-Token': '"*****"'}
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
        return send_tweets(tweet1, tweet2, tweet3)
    else:
        return print('No PL fixtures today')


def send_tweets(tweet, tweet2, tweet3):
    """Publishes tweets to timeline using Twitter API"""

    # Authorises Twitter API connection
    api = twitter_auth()

    # Sends tweets to timeline, depending on how many tweets created
    # Multiple tweets sent as a thread by responding to previous tweet
    if tweet3:
        first_tweet = api.update_status(tweet)
        first_id = first_tweet.id
        second_tweet = api.update_status(tweet2, first_id)
        second_id = second_tweet.id
        api.update_status(tweet3, second_id)
    elif tweet2:
        first_tweet = api.update_status(tweet)
        first_id = first_tweet.id
        api.update_status(tweet2, first_id)
    else:
        api.update_status(tweet)


def main():
    """Runs functions"""
    construct_fixtures_tweets()


if __name__ == "__main__":
    main()
