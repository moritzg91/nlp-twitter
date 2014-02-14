import json, nltk

from alchemyapi import AlchemyAPI
alchemyapi = AlchemyAPI()

with open('goldenglobes.json', 'r') as f:
	tweets = map(json.loads, f)

print len(tweets)

def find_tweets_by_user(tweets, username):
	ret = []
	for t in tweets:
		if (t['user']['screen_name'].lower() == username):
			ret.append(t['text'])
	return ret

def find_tweets_containing(tweets, keyword):
	ret = []
	for t in tweets:
		if keyword in t['text']:
			ret.append(t)
	return ret

def get_sentiment_of_tweets(tweet_list):
	resps = []
	for t in tweet_list:
		response = alchemyapi.sentiment('text',t['text'].encode('ascii','ignore'))
		if response['status'] != u'ERROR':
			if 'sentiment' in response:
				resps.append({'text': t['text'], 'sentiment': response['sentiment'] })
			elif 'docSentiment' in response:
				resps.append({'text': t['text'], 'sentiment': response['docSentiment'] })
	print resps
	return resps


#print find_tweets_containing(tweets, 'nominated')

def get_entities(tweet_text):
	tweet_text = tweet_text.encode('utf-8')
	tokens = nltk.word_tokenize(tweet_text)
	tagged = nltk.pos_tag(tokens)
	chunks = nltk.chunk.ne_chunk(tagged)
	print chunks
	
	entity_names = []
	for word_tuple in chunks.pos():
		if word_tuple[1] == 'PERSON' or word_tuple[1] == 'ORGANIZATION':
			entity_names.append(word_tuple[0])
	return entity_names

def find_winner_of(tweets, category_name):
	tweets_about_category = find_tweets_containing(tweets, category_name)
	# try not to eat up all of our alchemyAPI limits
	if len(tweets_about_category) > 200:
		tweets_about_category = tweets_about_category[:200]

	tagged_tweets = get_sentiment_of_tweets(tweets_about_category)

	good_tweets = []
	for r in tagged_tweets:
		if r['sentiment'] > 0.1:
			good_tweets.append(r['text'])

	entity_map = {}
	for gt in good_tweets:
		entities = get_entities(gt)
		for e in entities:
			if e in entity_map.keys():
				entity_map[e] += 1
			else:
				entity_map[e] = 1

	print entity_map
	return entity_map

#find_winner_of(tweets, 'director')