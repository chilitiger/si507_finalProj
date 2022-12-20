# %%
import secretKey
import requests
import json
import random
import sys
import re
import webbrowser

OMD_CACHE_FILENAME = "OMD_cache.json"
ITUNES_CACHE_FILENAME = "iTunes_cache.json"
RECOMMENDATION_CAHCE_FILENAME = "recommend_cache.json"

def open_cache(fileName):
    ''' opens the cache file if it exists and loads the JSON into
    a dictionary, which it then returns.
    if the cache file doesn't exist, creates a new cache dictionary
    Parameters
    ----------
    fileName: str
      The name of cache file
    Returns
    -------
    The opened cache
    '''
    try:
        cache_file = open(fileName, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict

def save_cache(cache_dict, fileName):
    ''' saves the current state of the cache to disk
    Parameters
    ----------
    cache_dict: dict
      The dictionary to save
    fileName: str
      The name of cache file
    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(fileName,"w")
    fw.write(dumped_json_cache)
    fw.close()

def construct_unique_key(baseurl, params):
    ''' constructs a key that is guaranteed to uniquely and 
    repeatably identify an API request by its baseurl and params
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dictionary
        A dictionary of param: param_value pairs
    Returns
    -------
    string
        the unique key as a string
    '''
    param_strings = []
    connector = '_'
    for k in params.keys():
        param_strings.append(f'{k}_{params[k].lower()}')
    param_strings.sort()
    unique_key = baseurl + connector +  connector.join(param_strings)
    return unique_key

def make_request(baseurl, params):
    '''Make a request to the Web API using the baseurl and params
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dictionary
        A dictionary of param: param_value pairs
    Returns
    -------
    string
        the results of the query as a Python object loaded from JSON
    '''
    response = requests.get(baseurl, params=params)
    return response.json()

def make_request_with_cache(baseurl, params, cache_dict, fileName, recommend = False, genre = "action"):
	'''Check the cache for a saved result for this baseurl+params
	combo. If the result is found, return it. Otherwise send a new 
	request, save it, then return it.
	Parameters
	----------
	baseurl: string
			The URL for the API endpoint
	params: dictionary
			A dictionary of param: param_value pairs
	cache_dict: dict
			The opened cache
	fileName: str
			The name of cache file
	Returns
	-------
	string
			the results of the query as a Python object loaded from JSON
	'''
	# check whether is recommandation procedure
	if recommend:
		request_key = genre
	else:
		request_key = construct_unique_key(baseurl, params)
	# check whether result is in cache file
	if request_key in cache_dict.keys():
		return cache_dict[request_key]
	else:
		if recommend:
			recommandResults = make_request(baseurl, params)
			recommand_data = []
			for result in recommandResults["results"]:
				if result['wrapperType'] == 'track' and result["kind"] == "feature-movie":
					recommand_data.append(result["trackName"])
			cache_dict[request_key] = recommand_data
		else:
			cache_dict[request_key] = make_request(baseurl, params)
		
		save_cache(cache_dict, fileName)
		return cache_dict[request_key]
		

def get_interested_movie(inGenre: str, cache_dict: dict, recommand:bool = False) -> set:
	'''	To get some recommendation based on user's search history
	Parameters
	----------
	inGenre: str
		The keyword to extract some user's search history
	cache_dict: dict
		The history file of user's search history
	recommand: bool
		An indicator to distinguish differenr cache_dict

	Returns
	-------
		A set to show what movies have been searched
	'''
	recommendationSet = set()
	if recommand:
		for genre in cache_dict.keys():
			if genre == inGenre:
				for i in cache_dict[genre]:
					recommendationSet.add(i)
	else:
		for search_results in cache_dict.values():
			for search_result in search_results["results"]:
				if search_result["primaryGenreName"] == inGenre:
					recommendationSet.add(search_result["trackName"])

	return recommendationSet

def yes(prompt):
    ''' Returns True if the answer is yes, False if it is no. Our version 
    insists on a proper answer (including convenient and fun options like
     "y", "yup", and "sure").
    '''
    if prompt == "yes" or prompt == "Yes" or prompt == "y" or prompt == "Y" or \
    prompt == "yup" or prompt == "Yup" or prompt == "sure" or prompt == "Sure" :
        return True
    else: 
        return False

def BingSearch(movieName: str) -> str:
  ''' The function to find the corresponding wikipedia url of specific movie
  Parameters
  ----------
  movieName:str
    The name of that movie
  Returns
  -------
    A str represented the URL of that movie
  '''
  subscription_key = secretKey.BingNewKey
  search_term = "movie" + movieName
  search_url = "https://api.bing.microsoft.com/v7.0/search"
  headers = {"Ocp-Apim-Subscription-Key" : subscription_key}
  params  = {"q": search_term, "mkt":"en-US", "category": "Entertainment_MovieAndTV", "sortBy": "Relevance"}
  response = requests.get(search_url, headers=headers, params=params)
  response.raise_for_status()
  response_data = response.json()
  search_results = response_data['webPages']["value"]
  for result in search_results:
    if len(re.findall(r"Wikipedia", result["name"])) != 0:
      movieURL = result["url"]
      break
  return movieURL

def main():
	OMD_CACHE = open_cache(OMD_CACHE_FILENAME)
	ITUNES_CACHE = open_cache(ITUNES_CACHE_FILENAME)
	RECOMMEND_CACHE = open_cache(RECOMMENDATION_CAHCE_FILENAME)

	OMDBaseUrl = "http://www.omdbapi.com/"
	iTunes_url = "https://itunes.apple.com/search"
	BingNews_url = "https://api.bing.microsoft.com/bing/v7.0/news"
	OMDParameter = {
		"apikey" : secretKey.OMDKey,
		"type" : "movie",
		"plot" : "short"
	}
	iTunesParams = {
		"media": "movie"
	}
	recommandParams = {
		"media": "movie",
		"entity": "movie",
		"attribute":"genreTerm"
	}
	BingParams = {
		"sortBy": "Relevance",
		"mkt": "en-US",
		"count": "3",
		"category": "Entertainment_MovieAndTV"
	}
	movieName = input("What is the name of the movie you are interested in? ")
	while(True):

		movieParams = {}
		for key, value in OMDParameter.items():
			movieParams[key] = value

		iTunes_params = {}
		for key, value in iTunesParams.items():
			iTunes_params[key] = value

		recommand_params = {}
		for key, value in recommandParams.items():
			iTunes_params[key] = value

		movieParams["t"] = movieName
		iTunes_params["term"] = movieName
		OMD_data = make_request_with_cache(OMDBaseUrl, movieParams, OMD_CACHE, OMD_CACHE_FILENAME)
		iTunes_data = make_request_with_cache(iTunes_url, iTunes_params, ITUNES_CACHE, ITUNES_CACHE_FILENAME)
		movieURL = BingSearch(movieName)
		# Find recommendations of movie
		if iTunes_data["resultCount"] == 0 or OMD_data["Response"] == "False":
			print(f"Error: Please type in correct movie name.")
			print(f"---------------------------------------------------------------")
			movieName = input("What is the name of the movie you are interested in? ")
		else:
			movieGenre = iTunes_data["results"][0]["primaryGenreName"]
			recommand_params["term"] = movieGenre
			recommand_data = make_request_with_cache(iTunes_url, recommand_params, RECOMMEND_CACHE, RECOMMENDATION_CAHCE_FILENAME, recommend= True, genre=movieGenre)

			recommandSet0 = get_interested_movie(movieGenre, RECOMMEND_CACHE, True)
			recommandSet1 = get_interested_movie(movieGenre, ITUNES_CACHE)
			recommandSet = set.union(recommandSet0, recommandSet1)
			recommandResult = random.sample(recommandSet, 5)

			displayTitle = OMD_data["Title"] + " (" + OMD_data["Year"] + ")"
			displayRating = OMD_data["imdbRating"]
			displayPlot = OMD_data["Plot"]
			displayRuntime = OMD_data["Runtime"]
			displayRated = OMD_data["Rated"]
			# Shows the search result
			print(f"\nBelow are the movie informations: \n")
			print(f"Title: {displayTitle}")
			print(f"Runtime: {displayRuntime}")
			print(f"Rated: {displayRated}")
			print(f"Rating: {displayRating}")
			print(f"Plot: {displayPlot}")
			print(f"Wikipedia link: {movieURL}")
			print(f"\nMore like this(similar movie recommendation): ")
			for i in range(len(recommandResult)):
				print(f"{i+1}. {recommandResult[i]}")
			print(f"---------------------------------------------------------------")
			endInnerLoop = True
			while(endInnerLoop):
				print(f"Choice Manual: ")
				print(f"1. Search another movie")
				print(f"2. Explore similar movie")
				print(f"3. Open current movie's wikipedia")
				print(f"4. Exit")
				choice = int(input("\nType in your choice: "))
				if choice == 1:
					movieName = input("\nWhat is the name of the movie you are interested in? ")
					endInnerLoop = False
				elif choice == 2:
					similarMovieChoice = int(input(f"Type in corresponding movie number: "))
					endIDX = True
					while(endIDX):
						if similarMovieChoice > len(recommandResult) or similarMovieChoice < 1:
							print("Error: Please type in correct choice num")
							similarMovieChoice = int(input(f"Type in corresponding movie number: "))
						else:
							movieName = re.sub(r"\([0-9]+\)", "", recommandResult[similarMovieChoice-1]).strip()
							endInnerLoop = False
							endIDX = False
				elif choice == 3:
					print('\nLaunching ', movieURL, " in web browser...")
					webbrowser.open_new(movieURL)
				elif choice == 4:
					print("Bye! :D")
					sys.exit(0)
				else:
					print("\nError: Please type in correct choice num")
			
	# format display data
	
if __name__ == '__main__':
    main()


