import json
import requests


MY_GCUBE_TOKEN = 'f08bb655-6465-4cdb-a5b2-7b7195cea1d7-843339462'


class TAGMEAnnotation:
    # An entity annotated by TAGME
    def __init__(self, d):
        # char offset (included)
        self.start = d['start']
        # char offset (not included)
        self.end = d['end']

        # annotation accuracy
        self.rho = d['rho']
        # spot-entity probability
        self.prior_prob = d['link_probability']

        # annotated text
        self.spot = d['spot']

        # Wikpedia entity info
        self.wiki_id = d['id']
        self.wiki_title = d['title']

    def json_dict(self):
        # Simple dictionary representation
        return {'wiki_id': self.wiki_id, 'wiki_title': self.wiki_title, 'start': self.start, 'end': self.end,
                'rho': self.rho, 'prior_prob': self.prior_prob}


class WATAnnotation:
    # An entity annotated by WAT

    def __init__(self, d):

        # char offset (included)
        self.start = d['start']
        # char offset (not included)
        self.end = d['end']

        # annotation accuracy
        self.rho = d['rho']
        # spot-entity probability
        self.prior_prob = d['explanation']['prior_explanation']['entity_mention_probability']
        # annotated text
        self.spot = d['spot']
        # Wikpedia entity info
        self.wiki_id = d['id']
        self.wiki_title = d['title']

    def json_dict(self):
        # Simple dictionary representation
        return {'wiki_title': self.wiki_title,
                'wiki_id': self.wiki_id,
                'start': self.start,
                'end': self.end,
                'rho': self.rho,
                'prior_prob': self.prior_prob
                }


def tagme_entity_linking(text):
    tagme_url = "https://tagme.d4science.org/tagme/tag"
    payload = [("gcube-token", MY_GCUBE_TOKEN),
               ("text", text),
               ("lang", 'en')]
    try:
        response = requests.get(tagme_url, params=payload)
        if response.json()['annotations']:
            tagme_annotations = [TAGMEAnnotation(a) for a in response.json()['annotations']]
            return [w.json_dict() for w in tagme_annotations]
    except:
        proccess_exception_here()


def wat_entity_linking(text):
    # Main method, text annotation with WAT entity linking system
    wat_url = 'https://wat.d4science.org/wat/tag/tag'
    payload = [("gcube-token", MY_GCUBE_TOKEN),
               ("text", text),
               ("lang", 'en'),
               ("tokenizer", "nlp4j"),
               ('debug', 9),
               ("method",
                "spotter:includeUserHint=true:includeNamedEntity=true:includeNounPhrase=true,prior:k=50,filter-valid,centroid:rescore=true,topk:k=5,voting:relatedness=lm,ranker:model=0046.model,confidence:model=pruner-wiki.linear")]
    try:
        response = requests.get(wat_url, params=payload)
        wat_annotations = [WATAnnotation(a) for a in response.json()['annotations']]
        return [w.json_dict() for w in wat_annotations]
    except:
        proccess_exception_here()


def proccess_exception_here():
    print("here is a timeout error!")


def pageid_map_qid(pageid):
    info_url = "https://en.wikipedia.org/w/api.php?action=query&prop=info&pageids=" + pageid + "&inprop=url&format=json"
    try:
        response = requests.get(info_url)
        result = response.json()["query"]["pages"]
        #print (result)
        if result:
            link = result[pageid]['fullurl']
            url = "https://tools.wmflabs.org/openrefine-wikidata/en/api?query=" + link
            #print (url)
            response = requests.get(url)
            results = response.json()["result"]
            if len(results) > 0:
                qid = results[0]['id']
                #print (qid)
                return qid
    except:
        proccess_exception_here()


def get_wikipedialink(pageid):
    info_url = "https://en.wikipedia.org/w/api.php?action=query&prop=info&pageids=" + pageid + "&inprop=url&format=json"
    try:
        response = requests.get(info_url)
        result = response.json()["query"]["pages"]
        # print(result)
        if result:
            link = result[pageid]['fullurl']
            return link
    except:
        print("get_wikipedialink problem", pageid)

def get_qid(wikipedia_link):
	url = "https://tools.wmflabs.org/openrefine-wikidata/en/api?query=" + wikipedia_link
	try:
		response = requests.get (url)
		results = response.json ()["result"]
		if results:
			qid = results[0]['id']
			return qid
	except:
		print ("get_qid problem", wikipedia_link)