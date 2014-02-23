import json, nltk
from alchemyapi import AlchemyAPI

class Award:
	def __init__(self, name, keyword):
		self.name = name
		self.keyword = keyword
		self.winner = None
		self.nominees = [None, None, None, None, None]
		self.winner_candidates = []

	def extract_most_likely_winner(self):
		if len(self.winner_candidates) > 0:
			return Counter(self.winner_candidates).most_common(1)[0][0]
		else:
			raise RuntimeError

class GoldenGlobeAnalyzer:
	def __init__(self, jsonFile, category_list = None):
		'''Initialize a GGA object and load the tweets contained in the json file'''
		self.tweets = []
		with open(jsonFile, 'r') as f:
			self.tweets = map(json.loads, f)

		self.awards = []

		for c in category_list:
			self.awards.append(Award(c))

		self.alchemyapi = AlchemyAPI()

	def find_tweets_by_user(self, username):
		'''Find all the tweets by a given user whose user name is :param username'''
		ret = []
		for t in self.tweets:
			if (t['user']['screen_name'].lower() == username.lower()):
				ret.append(t)
		return ret

	def find_tweets_containing(self, keyword):
		ret = []
		for t in self.tweets:
			if keyword in t['text']:
				ret.append(t)
		return ret

	def get_sentiment_of_tweets(self,tweet_list):
		resps = []
		for t in tweet_list:
			response = self.alchemyapi.sentiment('text',t['text'].encode('ascii','ignore'))
			if response['status'] != u'ERROR':
				if 'sentiment' in response:
					resps.append({'text': t['text'], 'sentiment': response['sentiment'] })
				elif 'docSentiment' in response:
					resps.append({'text': t['text'], 'sentiment': response['docSentiment'] })
		return resps

	def get_entities(tweet_text):
		tweet_text = tweet_text.encode('utf-8')
		tokens = nltk.word_tokenize(tweet_text)
		tagged = nltk.pos_tag(tokens)
		chunks = nltk.chunk.ne_chunk(tagged)
		print chunks
		
		entity_names = []
		for word_tuple in chunks.pos():
			print word_tuple
			if word_tuple[1] == 'PERSON' or word_tuple[1] == 'ORGANIZATION':
				entity_names.append(word_tuple[0])
		return entity_names

	# def find_winner_of(self, award):
	# 	tweets_about_category = self.find_tweets_containing(self.tweets, award.name)

	# 	# try not to eat up all of our alchemyAPI limits
	# 	if len(tweets_about_category) > 200:
	# 		tweets_about_category = tweets_about_category[:200]

	# 	tagged_tweets = self.get_sentiment_of_tweets(tweets_about_category)

	# 	good_tweets = []
	# 	for r in tagged_tweets:
	# 		if r['sentiment'] > 0.1:
	# 			good_tweets.append(r['text'])

	# 	entity_map = {}
	# 	for gt in good_tweets:
	# 		entities = self.get_entities(gt)
	# 		for e in entities:
	# 			if e in entity_map.keys():
	# 				entity_map[e] += 1
	# 			else:
	# 				entity_map[e] = 1

	# 	print entity_map
		return entity_map

	def find_winners(self, awardName):

		tweets_lst = []

		for tweet in self.tweets:
			if ("wins" in tweet["text"] or "won" in tweet["text"]) and "should" not in tweet["text"]:
				info = (tweet["text"].partition("http")[0])
				info = info.partition(":")[2]
				if "@" in info:
					info = info.partition("@")[2]
				info=info.replace("#","")
				info = info.replace('"','')
			tweets_lst.append(info)
		tweets_lst = list(set(tweets_lst))

		for i in tweets_lst:
			if "wins" in i:
				i = i.partition("wins")
			else:
				i = i.partition("won")
			winner = i[0]
			category = i[2].lower()
			for award in self.awards:
				if type(award.keyword) is str:
					if award.keyword in category:
						award.winner_candidates.append(winner)
						break
				elif type(award.keyword) is list:
					correctCategory = True
					for kw in award.keyword:
						if kw not in category:
							correctCategory = False
					if correctCategory:
						award.winner_candidates.append(winner)
						break

		for award in self.awards:
			award.extract_most_likely_winner()

		return


	def print_winner(self, award):
		print award.winner + "won " + award.name
		print "\n"

if __name__ == '__main__':

	categories = [
		"animatedFeatureFilm",
		"director",
		"foreignLanguagueFilm",
		"miniseries",
		"mpComed",
		"mpDrama",
		"originalScor",
		"originalSon",
		"actorInMiniseries",
		"actorInMPDram",
		"actorInMPComed",
		"supportingActorMP",
		"supportingActorMiniSeries",
		"actorTVDram",
		"actorTVComedy",
		"supportingActressInMP",
		"actressMiniSeries",
		"actressMPComedy =",
		"actressMPDrama ",
		"actressTVDrama ",
		"actressTVComedy =",
		"screenplay ",
		"tvDrama",
		"tvComedy "
	]

	gga = GoldenGlobeAnalyzer('goldenglobes.json', categories)