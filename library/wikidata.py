# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import re
from dataload import load_data
import json
import time
import requests
from base_search import get_all_triples

# Load resource
identifier_predicates, label_dict, predicate_frequencies_dict, entity_frequencies_dict, statements_dict = load_data()
upper_limit = 5000
# word pattern
predicate_pattern = re.compile('^P[0-9]*$')
entity_pattern = re.compile('^Q[0-9]*$')

#####################################################
###		Data fetching
#####################################################


# returns all statements that involve the given entity
def get_all_statements_of_entity(entity_id):
	entity_id = entity_id.strip()
	# check entity pattern
	# if not entity_pattern.match(entity_id.strip()):
	if len(re.findall('Q\d+', entity_id)) < 1:
		return False
	if statements_dict.get(entity_id, None) is not None:
		return statements_dict[entity_id]
	statements = []
	triples_sub, cardinality_sub = get_all_triples(entity_id, 0)  # entity as subject  Triples and the number of triples
	triples_obj, cardinality_obj = get_all_triples(entity_id, 1)  # entity as object   Triples and the number of triples

	if cardinality_sub + cardinality_obj > upper_limit:
		statements_dict[entity_id] = []
		return statements
	# iterate through all triples in which the entity occurs as the subject
	for triple in triples_sub:
		sub, pre, obj = triple
		# only consider triples with a wikidata-predicate or if it is an identifier predicate
		if not pre.startswith("http://www.wikidata.org/") or (wikidata_url_to_wikidata_id(pre) in identifier_predicates):
			continue
		# object is statement Statement is the object of a triplet in which the extracted entity acts as the subject
		if obj.startswith("http://www.wikidata.org/entity/statement/"):
			qualifier_statements = get_all_statements_with_qualifier_as_subject(obj)
			# When the object is statement and acts as qualifier, get all triples in which the object acts as the subject
			qualifiers = []
			for qualifier_statement in qualifier_statements:
				if qualifier_statement['predicate'] == "http://www.wikidata.org/prop/statement/" + wikidata_url_to_wikidata_id(pre):
						obj = qualifier_statement['object']
						# When the predicate in qualifier is P, the original statement is followed as the object
				elif is_entity_or_literal(wikidata_url_to_wikidata_id(qualifier_statement['object'])):
					# Check whether objects are normal URLs or date numbers added to qualifiers(qualifiers only contain predicate and objects).
					qualifiers.append({
						"qualifier_predicate":{
							"id": wikidata_url_to_wikidata_id(qualifier_statement['predicate'])
						}, 
						"qualifier_object":{	
							"id": wikidata_url_to_wikidata_id(qualifier_statement['object'])
						}})
			statements.append({'entity': {'id': wikidata_url_to_wikidata_id(sub)}, 'predicate': {'id': wikidata_url_to_wikidata_id(pre)}, 'object': {'id': wikidata_url_to_wikidata_id(obj)}, 'qualifiers': qualifiers})
		else:
			# If the object is an object entity, there is no qualifier
			statements.append({'entity': {'id': wikidata_url_to_wikidata_id(sub)}, 'predicate': {'id': wikidata_url_to_wikidata_id(pre)}, 'object': {'id': wikidata_url_to_wikidata_id(obj)}, 'qualifiers': []})
	# iterate through all triples in which the entity occurs as the object
	for triple in triples_obj:
		sub, pre, obj = triple
		if not sub.startswith("http://www.wikidata.org/entity/Q") or not pre.startswith("http://www.wikidata.org/") or wikidata_url_to_wikidata_id(pre) in identifier_predicates:
			continue
		if sub.startswith("http://www.wikidata.org/entity/statement/"):
			# Get a triplet with statement as the subject, and returns a triplet in which statement is the object
			statements_with_qualifier_as_object =  get_statement_with_qualifier_as_object(sub, process)
			# if no statement was found continue
			if not statements_with_qualifier_as_object:
				continue
			main_sub, main_pred, main_obj = statements_with_qualifier_as_object
			qualifier_statements = get_all_statements_with_qualifier_as_subject(sub)# Get the qualifier statements for which statement is the subject
			qualifiers = []
			for qualifier_statement in qualifier_statements:
				if wikidata_url_to_wikidata_id(qualifier_statement['predicate']) == wikidata_url_to_wikidata_id(main_pred):
					main_obj = qualifier_statement['object']
				elif is_entity_or_literal(wikidata_url_to_wikidata_id(qualifier_statement['object'])):
					qualifiers.append({
						"qualifier_predicate":{
							"id": wikidata_url_to_wikidata_id(qualifier_statement['predicate'])
						}, 
						"qualifier_object":{	
							"id": wikidata_url_to_wikidata_id(qualifier_statement['object'])
						}})
			statements.append({'entity': {'id': wikidata_url_to_wikidata_id(main_sub)}, 'predicate': {'id': wikidata_url_to_wikidata_id(main_pred)}, 'object': {'id': wikidata_url_to_wikidata_id(main_obj)}, 'qualifiers': qualifiers})
		else:
			statements.append({'entity': {'id': wikidata_url_to_wikidata_id(sub)}, 'predicate': {'id': wikidata_url_to_wikidata_id(pre)}, 'object': {'id': wikidata_url_to_wikidata_id(obj)}, 'qualifiers': []})
	# cache the data
	statements_dict[entity_id] = statements
	return statements


# check if the given wikidata object is an entity or a literal
def is_entity_or_literal(wd_object):
	# if entity_pattern.match(wd_object.strip()):
	if len(re.findall('Q\d+', wd_object.strip())) >= 1:
		return True
	if len(wd_object) == 32 and re.compile('^[A-Za-z0-9]*$').match(wd_object.strip()):
		return False
	return True


# fetch all statements where the given qualifier statement occurs as subject
def get_all_statements_with_qualifier_as_subject(qualifier):
	try:
		statements = []
		entity_id = qualifier.split('/')[-1].split('-')[0].upper()
		print("entity_id:", entity_id)
		triples, cardinality = get_all_triples(entity_id, 0)
		triples_new = []
		for old_en in triples:
			sub, pre, ob = old_en[:]
			if ob == qualifier:
				triples_new.append(old_en)
		for triple in triples_new:
			sub, pre, obj = triple
			if pre.startswith("http://www.wikidata.org/"):
				statements.append({'entity': sub, 'predicate': pre, 'object': obj})
		return statements
	except Exception as ex:
		return []


# fetch the statement where the given qualifier statement occurs as object
def get_statement_with_qualifier_as_object(qualifier):
	# triples, cardinality = document.search_triples("", "", qualifier)
	triples, cardinality = get_all_triples(qualifier, 1)
	for triple in triples:
		sub, pre, obj = triple
		# only consider triples with a wikidata-predicate
		if pre.startswith("http://www.wikidata.org/") and sub.startswith("http://www.wikidata.org/entity/Q"):
			return (sub, pre, obj)
	return False

# returns the frequency of the given predicate in wikidata
def predicate_frequency(predicate_id):
	if not(predicate_pattern.match(predicate_id.strip())):
		return 0
	if predicate_frequencies_dict.get(predicate_id) != None:
		return predicate_frequencies_dict[predicate_id]
	predicate = "http://www.wikidata.org/prop/direct/"+predicate_id

	partan = "https://query.wikidata.org/sparql?query=SELECT%0A%20%20%3Fitem%20%3FitemLabel%0A%20%20%3Fvalue%20%3FvalueLabel%0AWHERE%20%0A%7B%0A%20%20%3Fitem%20wdt%3A" + "{}" + "%20%3Fvalue%20%0A%20%20SERVICE%20wikibase%3Alabel%20%7B%20bd%3AserviceParam%20wikibase%3Alanguage%20%22%5BAUTO_LANGUAGE%5D%2Cen%22.%20%7D%0A%7D%0ALIMIT%2010&format=json"

	response = requests.get(partan.format(predicate_id))  # Query by the ID of the Entity
	results = response.json()  # json format
	print("len of results:", len(results))
	predicate_frequencies_dict[predicate_id] = len(results)
	return len(results)

# return the frequency of the given entity in wikidata
def entity_frequency(entity_id):
	if not(entity_pattern.match(entity_id.strip())):
		return 0
	if entity_frequencies_dict.get(entity_id) != None:
		return entity_frequencies_dict[entity_id]
	entity = "http://www.wikidata.org/entity/"+entity_id
	triples, cardinality = get_all_triples(entity_id, 0)
	entity_frequencies_dict[entity_id] = cardinality
	return cardinality

# return the english label that corresponds to the given wikidata_id
def wikidata_id_to_label(wikidata_id):
	if label_dict.get(wikidata_id) != None:
		return label_dict[wikidata_id]

	if not(entity_pattern.match(wikidata_id.strip())) and not(predicate_pattern.match(wikidata_id.strip())):
		return wikidata_id

	wikidata_url = "http://www.wikidata.org/entity/"+wikidata_id

	wikidata_id = wikidata_id.upper()
	response = requests.get(wikidata_url)
	results = response.json()  # json format
	try:
		if "P" in wikidata_id:
			print('results results:', results)
			en_label = results['entities'][wikidata_id]['labels']['en']['value']
			label_dict[wikidata_id] = en_label
			print('wikidata_id:{} | wikidata_label:{}'.format(wikidata_id, en_label))
		else:
			print('#' * 100)
			response = requests.get("https://www.wikidata.org/w/api.php?action=wbsearchentities&search=" + wikidata_id + "&language=en&limit=20&format=json")
			results = response.json()  # json format
			en_label = results['search'][0]['label']

		return en_label
	except Exception as ex:
		print("Error:", results['search'])


# get top-k hits for the given name for wikidata search
def name_to_wikidata_ids(name, limit=3):
	name = name.split('(')[0]

	request_successfull = False
	while not request_successfull:
		try:
			entity_ids = requests.get('https://www.wikidata.org/w/api.php?action=wbsearchentities&format=json&language=en&limit=' + str(limit) + '&search='+name).json()
			request_successfull = True
		except:
			time.sleep(5)
	results = entity_ids.get("search")
	if not results:
		return ""
	if not len(results):
		return ""
	res = []
	for result in results:
		res.append(result['id'])
	return res


# return if the given string is a literal or a date
def is_literal_or_date (answer): 
	return not('www.wikidata.org' in answer)


# convert the given month to a number
def convert_month_to_number(month):
	month = month.lower()
	for cur_index, cur_value in enumerate(["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]):
		if month.__eq__(cur_value):
			return '0' + str(cur_index + 1)


def convert_date_to_timestamp(date):
	sdate = date.split(" ")
	if len(sdate[0]) < 2:
		sdate[0] = "0" + sdate[0]
	return sdate[2] + '-' + convert_month_to_number(sdate[1]) + '-' + sdate[0] + 'T00:00:00Z'


# get the wikidata id of a wikidata url
def wikidata_url_to_wikidata_id(url):
	if not url:
		return False
	if "XMLSchema#dateTime" in url or "XMLSchema#decimal" in url:
		return url.split("\"", 2)[1].replace("+", "")
	if not('www.wikidata.org' in url):
		if re_mapping(url, re.compile('^[0-9][0-9][0-9][0-9]$')):
			return url + '-01-01T00:00:00Z'
		if re_mapping(url, re.compile('^[0-9]+ [A-z]+ [0-9][0-9][0-9][0-9]$')):
			return convert_date_to_timestamp(url)
		else:
			url = url.replace("\"", "")
			return url
	else:
		url_array = url.split('/')
		return url_array[len(url_array)-1]


# parse the given answer string and return a list of wikidata_id's
def parse_answers(answers_string):
	answers = answers_string.split(';')
	return [wikidata_url_to_wikidata_id(answer) for answer in answers]


def re_mapping(p, p1):
	return False if not(p1.match(p.strip())) else True



