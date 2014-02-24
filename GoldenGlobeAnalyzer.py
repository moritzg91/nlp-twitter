import json, nltk, operator, re
from alchemyapi import AlchemyAPI
from collections import Counter

class Award:
	def __init__(self, name, regex, long_name = ""):
		self.name = name ## eg. ActorInMiniseries
		self.re = regex ## eg. "animated" or ["actor","miniseries"]
		self.winner = ""
		self.nominees = ["None", "None", "None", "None", "None"]
		self.winner_candidates = [] ## internal use
		self.presenters = ["None","None"]
		self.long_name = long_name
		self.popularity = 0.0

	def extract_most_likely_winner(self):
		if len(self.winner_candidates) > 0:
			self.winner = Counter(self.winner_candidates).most_common(1)[0][0]
		else:
			self.winner = "None"

class GoldenGlobeAnalyzer:
	def __init__(self, jsonFile, category_list = None, debug = False):
		'''Initialize a GGA object and load the tweets contained in the json file'''
		self.debug = debug
		self._entity_count_cutoff = 80

		self.tweets = []
		with open(jsonFile, 'r') as f:
			self.tweets = map(json.loads, f)

		print "-- read tweets\n"

		self.awards = []

		for c in category_list:
			self.awards.append(Award(c[0],c[1],c[2]))

		self.hosts = [None,None]
		self.alchemyapi = AlchemyAPI()

	def _get_permutations_internal(self,lst):
		permutations = {}
		for i in range(len(lst)):
			for j in range(len(lst)):
				if i != j:
					name = lst[i] + " " + lst[j]
					permutations[name] = 0
		return permutations

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

	def get_sentiment_of_tweets(self,tweet_lump):
		response = self.alchemyapi.sentiment('text',tweet_lump.encode('ascii','ignore'))
		if response['status'] != u'ERROR':
			if 'sentiment' in response:
				return response['sentiment']
			elif 'docSentiment' in response:
				return response['docSentiment']
		return 0.0

	def get_entities(self,tweet_text):
		tweet_text = tweet_text.encode('utf-8')
		tokens = nltk.word_tokenize(tweet_text)
		tagged = nltk.pos_tag(tokens)
		chunks = nltk.chunk.ne_chunk(tagged)
		
		entity_names = []
		for word_tuple in chunks.pos():
			if word_tuple[1] == 'PERSON' or word_tuple[1] == 'ORGANIZATION':
				if word_tuple[0][0].lower() != "golden" and word_tuple[0][0].lower() != "globes" and word_tuple[0][0].lower() != "goldenglobes" and word_tuple[0][0].lower() != "best":
					entity_names.append(word_tuple[0])
		return entity_names

	def find_presenters(self):

		blacklist = ""
		for award in self.awards:
			blacklist += award.winner.lower()

		for award in self.awards:
			relevant = []
			cont = True

			for t in self.tweets:
				if re.findall(r"[pP]resent*",t["text"]) and re.findall(award.re,t["text"]):
					relevant.append(t)

			ent_dict = {}

			for tweet in relevant:
				ents = self.get_entities(tweet["text"])
				for e in ents:
					entity = e[0]
					if (entity.lower() not in award.long_name.lower()) and (entity.lower() not in blacklist):
						if entity in ent_dict:
							ent_dict[entity] += 1
							#print ent_dict[e]
						else:
							ent_dict[entity] = 1
						if ent_dict[entity] > 30: # cutoff to improve performance
							cont = False
				if not cont:
					break

			sorted_ents = sorted(ent_dict.iteritems(), key=operator.itemgetter(1), reverse = True)
			name_parts = []
			for i in range(min(len(sorted_ents),8)):
				name_parts.append(sorted_ents[i][0])

			presenter_idx = 0
			possible_name_combos = self._get_permutations_internal(name_parts)
			cont = True
			for tweet in relevant:
				for name in possible_name_combos:
					if name in tweet["text"]:
						possible_name_combos[name] += 1
						if possible_name_combos[name] > 0:
							award.presenters[presenter_idx] = name
							presenter_idx += 1
							if presenter_idx > 1:
								cont = False
								break
							possible_name_combos[name] -= 1000 # ugly hack but it works
				if not cont:
					break

			if award.presenters[0] == "None":
				for t in self.tweets:
					if re.findall(award.re,t["text"]):
						relevant.append(t)
				ent_dict2 = {}
				relevant_text = ""
				for r in relevant:
					relevant_text += r["text"] + "\n"

				response = self.alchemyapi.entities('text',relevant_text.encode('ascii','ignore'))
				if response['status'] == 'OK':
					for entity in response['entities']:
						ent_txt = entity["text"].encode('ascii','ignore')
						if ent_txt.lower() != "goldenglobes" and ent_txt.lower() != "golden globes":
							if ent_txt in ent_dict2:
								ent_dict2[ent_txt] += 1
							else:
								ent_dict2[ent_txt] = 1

				sorted_ents = sorted(ent_dict2.iteritems(), key=operator.itemgetter(1), reverse = True)
				for s in range(min(len(sorted_ents),2)):
					award.presenters[s] = sorted_ents[s][0]
					blacklist += " " + sorted_ents[s][0].lower()

			print "-- " + award.presenters[0] + ((" and " + award.presenters[1] ) if award.presenters[1] != "None" else "") + " presented " + award.long_name

		return

	def print_presenters(self):
		for award in self.awards:
			print award.presenters[0] + ((" and " + award.presenters[1] ) if award.presenters[1] != "None" else "") + " presented " + award.long_name

	def find_hosts(self):

		relevant = []
		new_tweets = []
		cont = True

		for t in self.tweets:
			if len(re.findall("host*",t["text"])) > 0:
				relevant.append(t)
		#	else:
		#		new_tweets.append(t)

		#self.tweets = new_tweets

		ent_dict = {}
		for tweet in relevant:
			ents = self.get_entities(tweet["text"])
			for e in ents:
				entity = e[0]
				if entity in ent_dict:
					ent_dict[entity] += 1
				else:
					ent_dict[entity] = 1
				if ent_dict[entity] > self._entity_count_cutoff: # cutoff to improve performance
					cont = False
			if not cont:
				break

		sorted_ents = sorted(ent_dict.iteritems(), key=operator.itemgetter(1), reverse = True)

		## two first names and two last names, so now we just need to figure out which of them belong together
		name_parts = []
		for i in range(4):
			name_parts.append(sorted_ents[i][0])

		host_idx = 0
		possible_name_combos = self._get_permutations_internal(name_parts)
		for tweet in relevant:
			for name in possible_name_combos:
				if name in tweet["text"]:
					possible_name_combos[name] += 1
					if possible_name_combos[name] > 10:
						print "-- " + name + " was a host"
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
		new_tweets = []

		for tweet in self.tweets:
			if ("wins" in tweet["text"] or "won" in tweet["text"]) and "should" not in tweet["text"]:
				info = (tweet["text"].partition("http")[0])
				info = info.partition(":")[2]
				if "@" in info:
					info = info.partition("@")[2]
				info=info.replace("#","")
				info = info.replace('"','')
				tweets_lst.append(info)
			else:
				new_tweets.append(tweet)
		tweets_lst = list(set(tweets_lst))
		self.tweets = new_tweets

		for i in tweets_lst:
			if "wins" in i:
				i = i.partition("wins")
			else:
				i = i.partition("won")
			winner = i[0]
			category = i[2]

			for award in self.awards:
				if re.findall(award.re,category):
					award.winner_candidates.append(winner)
					break

		for award in self.awards:
			award.extract_most_likely_winner()
			print award.winner + "won " + award.long_name

		return

	def print_winners(self):
		for award in self.awards:
			print award.winner + "won " + award.long_name
			print "\n"

	def find_nominees(self):

		blacklist = ""
		for award in self.awards:
			blacklist += award.winner.lower()

		for award in self.awards:
			relevant = []
			cont = True

			for t in self.tweets:
				if re.findall(r"([nN]ominated.*[fF]or)|([nN]ominee)",t["text"]) and re.findall(award.re,t["text"]) and "should" not in t["text"] and "wasn't" not in t["text"]:
					relevant.append(t)
				elif re.findall(r"\b[sS]hould.*[wW]on\b",t["text"]) and re.findall(award.re,t["text"]):
					relevant.append(t)

			ent_dict = {}
			relevant_text = ""
			for r in relevant:
				relevant_text += r["text"] + "\n"

			response = self.alchemyapi.entities('text',relevant_text.encode('ascii','ignore'))
			if response['status'] == 'OK':

				for entity in response['entities']:
					ent_txt = entity["text"].encode('ascii','ignore')
					if ent_txt.lower() != "goldenglobes" and ent_txt.lower() != "golden globes":
						if ent_txt in ent_dict:
							ent_dict[ent_txt] += 1
						else:
							ent_dict[ent_txt] = 1

			sorted_ents = sorted(ent_dict.iteritems(), key=operator.itemgetter(1), reverse = True)
			for s in range(min(len(sorted_ents),5)):
				award.nominees[s] = sorted_ents[s][0]
			print "The nominees for " + award.long_name + " are " + award.nominees[0] + ", " + award.nominees[1] + ", " + award.nominees[2] + ", " + award.nominees[3] + " and " + award.nominees[4]

	def find_popularity_of_winners(self):
		for award in self.awards:
			if award.winner != "None":
				relevant_text = ""
				for t in self.tweets:
					if award.winner in t["text"]:
						relevant_text += award.winner + '\n'
				award.popularity = self.get_sentiment_of_tweets(relevant_text)

		most_popular = self.awards[0]
		least_popular = self.awards[0]
		for award in self.awards:
			if award.popularity > most_popular.popularity:
				most_popular = award
			elif award.popularity < least_popular.popularity:
				least_popular = award

		print "-- The most popular winner was " + most_popular.winner + " and the least popular winner was " + least_popular.winner
		return

	def find_dress_opinions(self):
		_all_positive = []
		_all_negative = []
		people = []
		for award in self.awards:
			people.append(award.winner)
		for host in self.hosts:
			people.append(host.encode('ascii','ignore'))

		for person in people:
			if person != "None":
				relevant_txt = ""
				for t in self.tweets:
					if person in t["text"] and re.findall(r"\b[dD]ress\b",t["text"]):
						relevant_txt += t["text"]
				sentiment_score = self.get_sentiment_of_tweets(relevant_txt)
				if type(sentiment_score) is not float:
					#print person + " : " + str(sentiment_score["score"])
					if float(sentiment_score["score"]) > 0.15:
						_all_positive.append([sentiment_score["score"],person])
					elif sentiment_score != 0.0:
						_all_negative.append([sentiment_score["score"],person])
		
		_all_positive = sorted(_all_positive, key = lambda tup : tup[0])
		_all_negative = sorted(_all_negative, key = lambda tup : tup[0])

		print "People liked these people's dresses (in descending order)"
		for a in _all_positive:
			print " - " + a[1]

		print "People didn't like these people's dresses very much (in descending order)"
		for a in _all_negative:
			print " - " + a[1]

if __name__ == '__main__':

	categories = [
		["animatedFeatureFilm", 			r"\b[aA]nimated\b", 													"animated feature film"],
		["director", 						r"\b[dD]irector\b", 													"director"],
		["foreignLanguagueFilm",			r"\b[fF]oreign\b", 														"foreign language film"],
		["originalScore",					r"\b[sS]core\b", 														"original score"],
		["originalSong",					r"\b[sS]ong\b", 														"original song"],
		["actorTVDrama",					r"\b[aA]ctor.+?\b[tT][vV]\b.+?\b[dD]rama\b", 					"actor in a TV drama"],
		["actorTVComedy",					r"\b[aA]ctor.+?\b[tT][vV]\b.+?\b[cC]omedy\b", 					"actor in a TV comedy"],
		["supportingActorInMiniseries",		r"\b[sS]upporting [aA]ctor.+?\b[mM]ini.*", 								"supporting actor in mini series"],
		["actorInMiniseries",				r"\b[aA]ctor.+?\b[mM]ini", 												"actor in a mini series"],
		
		["actorInMPDrama",					r"\b[aA]ctor.+?\b[dD]rama\b", 									"actor in a motion picture - drama"],
		["actorInMPComedy",					r"\b[aA]ctor.+?\b[cC]omedy\b", 										"actor in a motion picture - comedy"],
		["supportingActorInMP",				r"\b[sS]upporting [aA]ctor.+?(\b[mM]otion [pP]icture\b)|(\b[Mm]ovie\b)|([mM][pP])", 	"supporting actor in a motion picture"],
		["supportingActressInMiniseries",	r"\b[sS]upporting [aA]ctress.+?\b[mM]ini", 								"supporting actress in a mini series"],

		["actressTVDrama", 					r"\b[aA]ctress.+?\b[tT][vV]\b.+?\b[dD]rama\b", 					"actress in a TV drama"],
		["actressTVComedy",					r"\b[aA]ctress.+?\b[tT][vV]\b.+?\b[cC]omedy\b", 				"actress in a TV comedy"],
		["actressInMiniseries",				r"\b[aA]ctress.+?\b[mM]ini.*", 											"actress in a mini series"],
		["actressInMPComedy", 				r"\b[aA]ctress.+?\b[cC]omedy\b", 	"actress in a motion picture - comedy"],
		["actressInMPDrama", 				r"\b[aA]ctress.+?\b[dD]rama\b", 		"actress in a motion picture - drama"],
		
		["supportingActressInMP",			r"\b[sS]upporting [aA]ctress\b", 	"supporting actress in a motion picture"],
		["screenplay",						r"\b[sS]creenplay\b", 													"screenplay"],
		["miniseries",						r"\b[mM]ini[- ]?[sS]eries\b", 													"miniseries"],
		["tvDrama",							r"\b[tT][vV].+?[dD]rama\b", 											"TV drama"],
		["tvComedy",						r"\b[tT][vV].+?[cC]omedy\b", 											"TV comedy"],
		["mpComedy",						r"\b[mM]otion [pP]icture.+?\b[cC]omedy\b",								"motion picture - comedy"],
		["mpDrama",							r"\b[mM]otion [pP]icture.+?\b[dD]rama\b", 								"motion picture - drama"],
	]

	gga = GoldenGlobeAnalyzer('goldenglobes.json', categories, True)

	gga.find_hosts()
	#gga.print_hosts()
	print "\n====================\n"
	gga.find_winners()
	#gga.print_winners()
	print "\n====================\n"
	gga.find_nominees()

	print "\n====================\n"

	gga.find_presenters()
	print "\n====================\n"
	gga.find_popularity_of_winners()
	print "\n====================\n"
	gga.find_dress_opinions()