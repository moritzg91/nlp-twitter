import urllib2
import json
import nltk
from nltk.tag import pos_tag
from collections import Counter 

animatedFeatureFilm=[] 
director=[] 
foreignLanguagueFilm=[] 
miniseries=[] 
mpComedy=[]
mpDrama=[] 
originalScore=[]
originalSong=[]
actorInMiniseries=[] 
actorInMPDrama=[]
actorInMPComedy=[]
supportingActorMP =[]
supportingActorMiniSeries=[] 
actorTVDrama=[]
actorTVComedy=[] 
supportingActressInMP=[] 
actressMiniSeries=[] 
actressMPComedy = [] 
actressMPDrama = []
actressTVDrama = []
actressTVComedy = [] 
screenplay = []
tvDrama =[]
tvComedy = []

listOfTweets=[]
listOfHosts=""

possibleHosts=[]


with open('goldenglobes.json', 'r') as f:
	tweets = map(json.loads, f) 



def find_host(possiblelist):
	possibleWinner = Counter(possiblelist).most_common()[0:2]
	if possibleWinner[1][1] > (possibleWinner[0][1] / 1.5):
		return possibleWinner
	else:
		return possibleWinner[0]



def find_winner(possiblelist):
	return Counter(possiblelist).most_common(1)[0][0]


def print_winner(winner, category):
	print find_winner(winner) + "won " + category



def extract_entity_names(t):
    entity_names = []
    
    if hasattr(t, 'node') and t.node:
        if t.node == 'NE':
            entity_names.append(' '.join([child[0] for child in t]))
        else:
            for child in t:
                entity_names.extend(extract_entity_names(child))
                
    return entity_names






for tweet in tweets:

	info = (tweet["text"].partition("http")[0])
	info = info.partition(":")[2]
	if "@" in info:
		info = info.partition("@")[2]
	info=info.replace("#","")
	info = info.replace('"','')

	if ("wins" in info or "won" in info) and "should" not in info:
		if "wins" in info:
			i = info.partition("wins")
		else:
			i = info.partition("won")
		winner = i[0]
		category = i[2].lower()

		if "animated" in category:
			animatedFeatureFilm.append(winner) 
		elif "director" in category:
			director.append(winner)
		elif "foreign" in category:
			foreignLanguagueFilm.append(winner)
		elif "score" in category:
			originalScore.append(winner)
		elif "song" in category:
			originalSong.append(winner)
		elif "screenplay" in category:
			screenplay.append(winner)
		elif "actor" in category:
			if "motion picture" in category:
				if "drama" in category:
					actorInMPDrama.append(winner)
				elif "comedy" in category:
					actorInMPComedy.append(winner)
				elif "supporting" in category:
					supportingActorMP.append(winner)
			elif "mini" in category:
				if "supporting" in category or "tv"  in category or "movie" in category:
					supportingActorMiniSeries.append(winner)
				else:
					actorInMiniseries.append(winner)
			elif "tv" in category:
				if "comedy" in category:
					actorTVComedy.append(winner)
				else:
					actorTVDrama.append(winner)
		elif "actress" in category:
			if "motion picture" in category:
				if "drama" in category:
					actressMPDrama.append(winner)
				elif "comedy" in category:
					actressMPComedy.append(winner)
				elif "supporting" in category:
					supportingActressInMP.append(winner)
			elif "mini" in category:
					actressMiniSeries.append(winner)
			elif "tv" in category:
				if "comedy" in category:
					actressTVComedy.append(winner)
				else:
					actressTVDrama.append(winner)
		elif "motion picture" in category:
			if "comedy" in category:
				mpComedy.append(winner)
			elif "drama" in category:
				mpDrama.append(winner)
		elif "miniseries" in category:
			miniseries.append(winner)
		elif "tv" in category:
			if "comedy" in category:
				tvComedy.append(winner)
			elif "drama" in category:
				tvDrama.append(winner)


	elif ("hosting" in info):
		info=info.partition("hosting")[0]
		listOfHosts = listOfHosts + info





tokens = nltk.word_tokenize(listOfHosts)		
tagged_sent = pos_tag(tokens)
hostTree = nltk.ne_chunk(tagged_sent, binary=True)
hosts = find_host(extract_entity_names(hostTree))

print "\n"
print "The hosts of the Golden Globes this year are " + hosts[0][0] + " and " + hosts[1][0] +"."
print "\n"


print_winner(animatedFeatureFilm, "best animated feature.")
print_winner(director, "best director.")
print_winner(foreignLanguagueFilm, "best foreign languague film.")
print_winner(miniseries, "best miniseries.")
print_winner(mpComedy, "best motion picture - comedy or musical.")
print_winner(mpDrama, "best motion picture - drama.")
print_winner(originalScore, "best original score")
print_winner(originalSong, "best original song.")
print_winner(actorInMiniseries, "best actor in a miniseries.")
print_winner(actorInMPDrama, "best actor in a motion picture - drama.")
print_winner(actorInMPComedy, "best actor in a motion picture - drama.")
print_winner(supportingActorMP, "best supporting actor in a motion picture.")
print_winner(supportingActorMiniSeries, "best supporting actor in a miniseries.")
print_winner(actorTVDrama, "best actor in a TV drama.")
print_winner(actorTVComedy, "best actor in a TV comedy.")
print_winner(supportingActressInMP, "best supporting actress in a motion picture.")
print_winner(actressMiniSeries, "best actress in a miniseries.")
print_winner(actressMPDrama, "best actress in a motion picure - drama.")
print_winner(actressMPComedy, "best actress in a motion picture - comedy.")
print_winner(actressTVDrama, "best actress in a TV drama.")
print_winner(actressTVComedy, "best actress in a TV comedy.")
print_winner(screenplay, "best screenplay.")
print_winner(tvComedy, "best TV comedy.")
print_winner(tvDrama, "best TV drama.")


# def find_category(tweetlist):
# 	possibleCat=[]
# 	for tweet in tweetlist:
# 		if "wins" in tweet:
# 			category = tweet.partition("wins ")[2]
# 		else:
# 			category = tweet.partition("won ")[2]
# 		category.replace("for ","",1)
# 		category.lower()
# 		if category.startswith("best "):
# 			possibleCat.append(category.partition(" for")[0])

# 	totalcats=[]

# 	for cat in Counter(possibleCat).most_common():
# 		if cat[1] > 1:
# 			totalcats.append(cat[0])

# 	return list(set(totalcats))





