import tweepy
import json
import sys
import re
import redis

class QueueListener(tweepy.StreamListener):

    def __init__(self, time_gap):
        self.queue = []
        self.time_gap = time_gap
        self.end_time = 10 ** 100

    def on_data(self, data):
        tweet = json.loads(data)
        if 'timestamp_ms' in tweet.keys():
            current_time = int(tweet['timestamp_ms'])   
            self.end_time = min(self.end_time, current_time)

            if current_time > self.end_time + self.time_gap:
                #have a tweet past it's end time
                return False

            #only push a tweet in queue if it has the lang en
            if 'lang' in tweet.keys() and tweet['lang'] == 'en':
                self.queue.append(tweet)

        return True

    def on_error(self):
        print(status)

    def get_queue(self):
        return self.queue

class TwitterData(object):

    def __init__(self, _consumer, _consumer_secret, _acces, _acces_secret, duration):
        self.consumer_key = _consumer
        self.consumer_secret = _consumer_secret
        self.access_token = _acces
        self.access_token_secret = _acces_secret

        self.auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
        self.auth.set_access_token(self.access_token, self.access_token_secret)

        #number of ms to process the feed
        self.duration = duration * 1000;

    def check_credentials(self):
        api = tweepy.API(self.auth)
        public_tweets = api.home_timeline()

    def get_stream(self):
        listen = QueueListener(self.duration)
        stream = tweepy.Stream(self.auth, listen)
        #sample the feed
        stream.sample()
        stream.disconnect()
        for tweet in listen.get_queue():
            tweet_words = filter(None, re.split("[, \-!?]+", tweet['text'].rstrip('\n')))
            for word in tweet_words:
                yield word.lower()

def main():

    if len(sys.argv) != 4:
        sys.exit('Usage: %s num_seconds num_requested_words stopwords_file_path' % sys.argv[0])

    #get arguments from argv
    num_seconds = float(sys.argv[1])
    num_requested_words = int(sys.argv[2])
    stopwords_file_path = sys.argv[3]

    # (consumer_key, consumer_secret, access_token, access_token_secret)
    with open("keys.json") as keys_file:
        keys = json.loads(keys_file.read());

    twitter = TwitterData(keys["consumer_key"],
            keys["consumer_secret"],
            keys["access_token"],
            keys["access_token_secret"],
            num_seconds)

    twitter.check_credentials()
    stop_words_list = []
    with open(stopwords_file_path) as f:
        stop_words_list = f.readlines()

    stop_words_hash = {word.rstrip('\n') for word in stop_words_list}

    # init redis
    r = redis.StrictRedis(host='tagcloud_db_1', port=6379, db=0)

    word_frequencies = dict()

    for keys in r.keys('*'):
        r.delete(keys)

    for word in twitter.get_stream():
        if word not in stop_words_hash:
            r.zincrby('word_counts', word, 1)
    top_words = []
    other_count = 0
    print(r.keys('*'))

    for item in r.zrevrangebyscore('word_counts', 10**100, 0,withscores=True):
        if num_requested_words > 0:
            top_words.append({'word': item[0].decode('UTF-8'), 'count': item[1]})
        else:
            other_count += item[1]
        num_requested_words -= 1
        #top_words.append({'word': word, 'count': word_frequencies[word]})

    top_words.append({'word': 'other_words', 'count': other_count})
    print(json.dumps(top_words, indent=4))
    return 0

if __name__=="__main__":
    main()
