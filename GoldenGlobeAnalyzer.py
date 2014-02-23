import json, nltk, operator, re
from alchemyapi import AlchemyAPI
from collections import Counter

class Award:
	def __init__(self, name, keyword):
		self.name = name ## eg. ActorInMiniseries
		self.keyword = keyword ## eg. "animated" or ["actor","miniseries"]
		self.winner = None 
		self.nominees = [None, None, None, None, None]
		self.winner_candidates = [] ## internal use
		self.winner_str = name ## eg. "best actor in a miniseries."

	def extract_most_likely_winner(self):
		if len(self.winner_candidates) > 0:
			self.winner = Counter(self.winner_candidates).most_common(1)[0][0]
		else:
			self.winner = "None"

class GoldenGlobeAnalyzer:
	def __init__(self, jsonFile, category_list = None):
		'''Initialize a GGA object and load the tweets contained in the json file'''
		self.tweets = []
		with open(jsonFile, 'r') as f:
			self.tweets = map(json.loads, f)

		print "-- read tweets\n"

		self.awards = []

		for c in category_list:
			print c
			self.awards.append(Award(c[0],c[1]))

		self.hosts = [None,None]
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

	def get_entities(self,tweet_text):
		tweet_text = tweet_text.encode('utf-8')
		tokens = nltk.word_tokenize(tweet_text)
		tagged = nltk.pos_tag(tokens)
		chunks = nltk.chunk.ne_chunk(tagged)
		
		entity_names = []
		for word_tuple in chunks.pos():
			if word_tuple[1] == 'PERSON' or word_tuple[1] == 'ORGANIZATION':
				if word_tuple[0][0].lower() != "golden" and word_tuple[0][0].lower() != "globes" and word_tuple[0][0].lower() != "goldenglobes":
					entity_names.append(word_tuple[0])
		return entity_names

	def find_hosts(self):
		def _get_permutations_internal(lst):
			permutations = {}
			for i in range(len(lst)):
				for j in range(len(lst)):
					if i != j:
						name = lst[i] + " " + lst[j]
						permutations[name] = 0
			return permutations

		relevant = []
		cont = True

		for t in self.tweets:
			if len(re.findall("host*",t["text"])) > 0:
				relevant.append(t)

		ent_dict = {}
		for tweet in relevant:
			ents = self.get_entities(tweet["text"])
			for e in ents:
				if e in ent_dict:
					ent_dict[e] += 1
					#print ent_dict[e]
				else:
					ent_dict[e] = 1
				if ent_dict[e] > 100: # cutoff to improve performance
					cont = False
			if not cont:
				break

		sorted_ents = sorted(ent_dict.iteritems(), key=operator.itemgetter(1), reverse = True)
		#print sorted_ents

		## two first names and two last names, so now we just need to figure out which of them belong together
		name_parts = []
		for i in range(4):
			name_parts.append(sorted_ents[i][0][0])

		host_idx = 0
		possible_name_combos = _get_permutations_internal(name_parts)
		for tweet in self.tweets:
			for name in possible_name_combos:
				if name in tweet["text"]:
					possible_name_combos[name] += 1
					if possible_name_combos[name] > 10:
						self.hosts[host_idx] = name
						host_idx += 1
						if host_idx > 1:
							return
						possible_name_combos[name] -= 1000 # ugly hack but it works
		return

	def print_hosts(self):
		for h in self.hosts:
			print h + " was a host\n"

	def find_winners(self):

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
		
		#print len(tweets_lst)

		for i in tweets_lst:
			if "wins" in i:
				i = i.partition("wins")
			else:
				i = i.partition("won")
			winner = i[0]
			category = i[2].lower()
			#print category
			#print winner
			for award in self.awards:
				#print award.name
				print award.keyword
				if type(award.keyword) == str:
					if award.keyword in category:
						#print winner
						award.winner_candidates.append(winner)
						break
				elif type(award.keyword) == list:
					correctCategory = True
					for kw in award.keyword:
						if kw not in category:
							correctCategory = False
					if correctCategory:
						#print winner
						award.winner_candidates.append(winner)
						break

		for award in self.awards:
			award.extract_most_likely_winner()

		return

	def print_winners(self):
		for award in self.awards:
			print award.winner + "won " + award.name
			print "\n"

if __name__ == '__main__':

	## TODO: use regex instead of keyword matching (more precise)
	categories = [
		["animatedFeatureFilm", "animated"],
		["director", "director"],
		["foreignLanguagueFilm","foreign"],
		["originalScore","score"],
		["originalSong","song"],
		["supportingActorInMiniseries",["actor","mini","supporting"]],
		["actorInMiniseries",["actor","mini"]],
		["actorInMPDrama",["actor","motion picture","drama"]],
		["actorInMPComedy",["actor","motion picture","comedy"]],
		["supportingActorInMP",["actor","supporting","motion picture"]],
		["actorTVDrama",["actor","tv","drama"]],
		["actorTVComedy",["actor","tv","comedy"]],
		["supportingActressInMiniseries",["actress","mini","supporting"]],
		["actressInMiniseries",["actress","mini"]],
		["actressInMPComedy", ["actress","motion picture","comedy"]],
		["actressInMPDrama", ["actress","motion picture","drama"]],
		["supportingActorInMP",["actress","supporting","motion picture"]],
		["actressTVDrama", ["actress","tv","drama"]],
		["actressTVComedy",["actress","tv","comedy"]],
		["screenplay","screenplay"],
		["miniseries","miniseries"],
		["tvDrama",["tv","drama"]],
		["tvComedy",["tv","comedy"]],
		["mpComedy",["motion picture","comedy"]],
		["mpDrama",["motion picture","drama"]],
	]

	gga = GoldenGlobeAnalyzer('goldenglobes.json', categories)

	gga.find_hosts()
	gga.print_hosts()

	#gga.find_winners()
	#gga.print_winners()