import json

with open('goldenglobes.json', 'r') as f:
	tweets = map(json.loads, f)

print len(tweets)

def find_tweets_by_user(tweets, username):
	ret = []
	for t in tweets:
		if (t['user']['screen_name'].lower() == username):
			ret.append(t['text'])
	return ret

