# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys
import json
import warnings
import requests
import time
sys.path.append("library")
import string_conversions as string
import graph_processing as gp
import glove_similarity as spacy 
import wikidata as wd
import telegram_api as telegram

#####################################################
# Candidate queue creation
#####################################################


def update_data(in_data, pp=None):
	if pp is None:
		dict_candidate = {
			'predicate': None
		}
		dict_candidate_1 = {
			'entity': None
		}
	else:
		dict_candidate = {
			pp[0]: None
		}
		dict_candidate_1 = {
			pp[1]: None
		}

	for en_dex, en in enumerate(in_data):
		if en_dex == 1:
			if isinstance(en, list) and len(en) > 1:
				dict_candidate['predicate'] = en[0]
				dict_candidate_1['entity'] = en[1]
			else:
				dict_candidate['predicate'] = en
				dict_candidate_1['entity'] = en
		else:
			if en[0] not in dict_candidate:
				if len(en) > 2:
					dict_candidate[en[0]] = en[1]
					dict_candidate_1[en[0]] = en[2]
				else:
					dict_candidate[en[0]] = en[1]
					dict_candidate_1[en[0]] = en[1]
	return [dict_candidate, dict_candidate_1]

# fetching data from online wikidata dump
def build_candidate_priority_queue_one_entity(entity_id):
	candidate_priority_queue_one_entity = []
	statements = wd.get_all_statements_of_entity(entity_id)
	# error handling
	if not statements:
		return []
	for statement in statements:
		# entity is the object of the statement
		if entity_id.__eq__(statement['object']['id']):
			entity_label = wd.wikidata_id_to_label(statement['entity']['id'])
			predicate_label = wd.wikidata_id_to_label(statement['predicate']['id'])
			candidate_priority_queue_one_entity.extend(update_data([["type", 'predicate', 'entity'],
										 statement['predicate']['id'], ['label', predicate_label, entity_label],
										 ['statement', statement]]))

		# entity is the subject of the statement
		else:
			object_label = wd.wikidata_id_to_label(statement['object']['id'])
			predicate_label = wd.wikidata_id_to_label(statement['predicate']['id'])
			candidate_priority_queue_one_entity.extend(update_data([["type", 'predicate', 'entity'],
																	statement['predicate']['id'],
																	['label', predicate_label, object_label],
																	['statement', statement]]))
		# include the qualifiers
		if statement['qualifiers']:
			for qualifier in statement['qualifiers']:
				qualifier_object_label = wd.wikidata_id_to_label(qualifier['qualifier_object']['id'])
				qualifier_predicate_label = wd.wikidata_id_to_label(qualifier['qualifier_predicate']['id'])
				candidate_priority_queue_one_entity.extend(update_data([["type", 'qualifier_object', 'qualifier_predicate'],
																		qualifier['qualifier_object']['id'],
																		['label', qualifier_object_label, qualifier_predicate_label],
																		['statement', statement]], ['qualifier_object', 'qualifier_predicate']))
	return candidate_priority_queue_one_entity


# fetching data from online wikidata dump
def fetch_candidate_from_online_wikidata(entity_id):
	candidate__entity = []
	statements = wd.get_all_statements_of_entity(entity_id)
	# error handling
	if not statements:
		return []
	for statement in statements:
		# entity is the object of the statement
		if entity_id == statement['object']['id']:

			entity_label = wd.wikidata_id_to_label(statement['entity']['id'])
			predicate_label = wd.wikidata_id_to_label(statement['predicate']['id'])
			candidate__entity.append({'type': 'predicate', 'predicate': statement['predicate']['id'], 'label': predicate_label,  'statement': statement})
			candidate__entity.append({'type': 'entity', 'entity': statement['entity']['id'], 'label': entity_label, 'statement': statement})
			#
			candidate__entity.extend(update_data([["type", 'predicate', 'entity'],
												  [statement['predicate']['id'], statement['entity']['id']],
												  ['label', predicate_label, entity_label],
												  ['statement', statement]]))

		# entity is the subject of the statement
		else:
			object_label = wd.wikidata_id_to_label(statement['object']['id'])
			predicate_label = wd.wikidata_id_to_label(statement['predicate']['id'])
			candidate__entity.append({'type': 'predicate', 'predicate': statement['predicate']['id'], 'label': predicate_label,  'statement': statement})
			candidate__entity.append({'type': 'entity', 'entity': statement['object']['id'], 'label': object_label, 'statement': statement})
			candidate__entity.extend(update_data([["type", 'predicate', 'entity'],
											  [statement['predicate']['id'], statement['object']['id']],
											  ['label', predicate_label, object_label],
											  ['statement', statement]]))

		# include the qualifiers
		if statement['qualifiers']:
			for qualifier in statement['qualifiers']:
				qualifier_object_label = wd.wikidata_id_to_label(qualifier['qualifier_object']['id'])
				qualifier_predicate_label = wd.wikidata_id_to_label(qualifier['qualifier_predicate']['id'])
				candidate__entity.append({'type': 'qualifier_object', 'qualifier_object': qualifier['qualifier_object']['id'], 'label': qualifier_object_label, 'statement': statement})
				candidate__entity.append({'type': 'qualifier_predicate', 'qualifier_predicate': qualifier['qualifier_predicate']['id'], 'label': qualifier_predicate_label,  'statement': statement})
				candidate__entity.extend(update_data([["type", 'qualifier_object', 'qualifier_predicate'],
												  [qualifier['qualifier_object']['id'], qualifier['qualifier_predicate']['id']],
												  ['label', qualifier_object_label, qualifier_predicate_label],
												  ['statement', statement]], ['qualifier_object', "qualifier_predicate"]))

	return candidate__entity




def build_candidate_queue(graph):
	candidate_priority_queue = []
	for node in list(graph.nodes(data=True)):
		if not node[1]['type'].__eq__('predicate'):
			candidate_priority_queue.extend(fetch_candidate_from_online_wikidata(node[0]))
	return candidate_priority_queue

# return all found entities 
def tagme_get_all_entities(utterance, tagmeToken):
	request_successfull = False
	while not request_successfull:
		try:
			print("tagmeToken:", tagmeToken)
			# ##################################################################
			tagme_url = "https://tagme.d4science.org/tagme/tag"
			payload = [("gcube-token", "f08bb655-6465-4cdb-a5b2-7b7195cea1d7-843339462"),
					   ("text", utterance),
					   ("lang", 'en')]
			response = requests.get(tagme_url, params=payload)
			# results = json.loads(requests.get('https://tagme.d4science.org/tagme/tag?lang=en&gcube-token=' + tagmeToken + '&text=' + utterance).content)
			results = json.loads(response.content)
			request_successfull = True
		except Exception as ex:
			print('error:', utterance, ex)
			time.sleep(5)
	entities = []
	for result in results["annotations"]:
		try:
			wikidata_ids = wd.name_to_wikidata_ids(result['title'])
		except:
			continue
		for wikidata_id in wikidata_ids:
			entities.append({'title': result['title'], 'spot': result['spot'], 'link_probability': result['link_probability'], 'wikidata_id': wikidata_id})
	return entities


def question_is_existential(question):
	key_w = ['is', 'are', 'was', 'were', 'am', 'be', 'being', 'been', 'did', 'do', 'does', 'done', 'doing', 'has', 'have', 'had', 'having']
	key_w_1 = list(map(lambda x: x.upper(), key_w))
	key_w.extend(key_w_1)
	for cur_key in key_w:
		if question.startswith(cur_key):
			return True
	return False

# get the priors for the given predicate
def priors_of_predicate(predicate, max_predicate_priors=18608694):
	predicate = predicate.split('-')[0]
	# do not consider these frequencies (instance_of, cites, author_name_string)
	if predicate in ['P31', 'P2860', 'P2093']:
		return 0
	predicate_frequency = wd.predicate_frequency(predicate)
	return float(predicate_frequency)/float(max_predicate_priors)

# get the priors for the given entity
def priors_of_entity(entity, max_entity_priors=10292):
	entity_frequency = wd.entity_frequency(entity)
	return float(entity_frequency)/float(max_entity_priors)

#####################################################
###		Fagins algorithm
#####################################################

def fagins_algorithm(queue1, queue2, queue3, hyperparameters, k=3):
	h1, h2, h3 = hyperparameters
	queue1_seen_ids = []
	queue2_seen_ids = []
	queue3_seen_ids = []
	length = len(queue1)

	for i in range(length):
		queue1_seen_ids.append(queue1[i]['id'])
		queue2_seen_ids.append(queue2[i]['id'])
		queue3_seen_ids.append(queue3[i]['id'])
		# returns true if k items are shared among all queues
		if k_items_shared(queue1_seen_ids, queue2_seen_ids, queue3_seen_ids, k=k):
			break
	candidates = []
	seen_ids = list(set(queue1_seen_ids + queue2_seen_ids + queue3_seen_ids))
	for item_id in seen_ids:
		candidate = next((x for x in queue1 if x['id'] == item_id), None)
		prop1 = next((x for x in queue1 if x['id'] == item_id), None)['score']
		prop2 = next((x for x in queue2 if x['id'] == item_id), None)['score']
		prop3 = next((x for x in queue3 if x['id'] == item_id), None)['score']
		score = h1 * prop1 + h2 * prop2 + h3 * prop3
		candidates.append({'statement': candidate['statement'], 'candidate': candidate['candidate'], 'type': candidate['type'], 'score': score})

	top_candidates = sorted(candidates, key=lambda j: j['score'], reverse=True)
	top_candidates = top_candidates[:k]
	return top_candidates

# returns true if k items are shared among all queues
def k_items_shared(queue1_seen_ids, queue2_seen_ids, queue3_seen_ids, k=3):
	shared_count = 0
	for item_id in queue1_seen_ids:
		if item_id in queue2_seen_ids and item_id in queue3_seen_ids:
			shared_count += 1
	if shared_count >= k:
		return True
	else:
		return False

# for the given question word, determine the top k matching candidates
def determine_attributes(candidates, context, turn): # Relevance to context
	# The application refers to the node graph in the expanded graph refers to the initial subgraph (first question)
	for candidate in candidates:
		# create a temporal context and include the candidates' statement there
		# Candidate Queue is a list of all neighbor nodes stored
		# The Temp Graph here is just to compute those three similarities
		# All candidates are temporarily added to it
		temp_context = context.copy()
		# Add the candidates to the current context
		temp_context = gp.expand_context_with_statements(temp_context, [candidate['statement']])
		# Return a list of entity nodes in the current graph that are the words in the question or the answer
		entity_nodes = gp.get_all_qa_nodes(temp_context)
		if candidate['type'] == 'entity':
			total_weighted_distance = 0
			for entity_node in entity_nodes:
				# increase distance by 1 to avoid zero division
				# A temporary context containing the candidates
				distance = gp.get_distance(temp_context, candidate['entity'], entity_node[0])
				total_weighted_distance += float(1/float(distance)) * (float(1.0) if entity_node[1]['turn'] == 1 else float(turn) / (turn-1) )
			context_relevance = total_weighted_distance / float(len(entity_nodes))
			priors = priors_of_entity(candidate['entity'])
		elif candidate['type'] == 'qualifier_object':
			total_weighted_distance = 0
			for entity_node in entity_nodes:
				# increase distance by 1 to avoid zero division
				distance = gp.get_distance(temp_context, candidate['qualifier_object'], entity_node[0]) 
				total_weighted_distance += float(1/float(distance)) * (float(1.0) if entity_node[1]['turn'] == 1 else float(turn) / (turn-1))
			context_relevance = total_weighted_distance / float(len(entity_nodes))
			priors = priors_of_entity(candidate['qualifier_object'])
		elif candidate['type'] == 'predicate':
			# priors = priors_of_predicate(candidate['predicate'])
			total_weighted_distance = 0
			for entity_node in entity_nodes:
				# every predicate label should be unique (to differ between them in the graph); predicate should already be in as in context
				predicate_label = candidate['predicate'] + "-" + str(gp.predicate_nodes[candidate['predicate']]-1)
				distance = gp.get_distance(temp_context, predicate_label, entity_node[0]) 		
				total_weighted_distance += float(1/float(distance)) * (float(1.0) if entity_node[1]['turn'] == 1 else float(turn) / (turn-1))
			context_relevance = total_weighted_distance / float(len(entity_nodes))
			priors = priors_of_predicate(candidate['predicate'])
		elif candidate['type'] == 'qualifier_predicate':
			total_weighted_distance = 0
			for entity_node in entity_nodes:
				# every predicate label should be unique (to differ between them in the graph); predicate should already be in as in context
				predicate_label = candidate['qualifier_predicate'] + "-" + str(gp.qualifier_predicate_nodes[candidate['qualifier_predicate']]-1)
				distance = gp.get_distance(temp_context, predicate_label, entity_node[0]) 
				total_weighted_distance += float(1/float(distance)) * (float(1.0) if entity_node[1]['turn'] == 1 else float(turn) / (turn-1))
			context_relevance = total_weighted_distance / float(len(entity_nodes))
			priors = priors_of_predicate(candidate['qualifier_predicate'])
			# A new key score is added to the candidate
		candidate['score'] = {'context_relevance': context_relevance , 'priors': priors}
	return candidates

def determine_matching_similarity(question_word, candidate, is_question_entity=False): # Relevance to question
	if is_question_entity:
		matching_similarity = question_word['link_probability']
		return matching_similarity
	else:
		if not candidate['label']:
			return 0
		label = wd.wikidata_id_to_label(candidate['label'])

		matching_similarity = spacy.similarity_word2vec(question_word, label)
		return matching_similarity

def determine_top_candidates(candidates_with_scores, frontier_hyperparameters, k=3): # KG priors
	# Candidates_with_scores here refers to evary candidate node[score:relevance to context][similarity:relevance to question]
	h1, h2, h3 = frontier_hyperparameters
	matching_similarity_queue = []
	for counter, candidate in enumerate(candidates_with_scores):
		# index + candidate[]
		matching_similarity_queue.append({'id': counter, 'candidate': candidate[candidate['type']], 'score': candidate['score']['matching_similarity'], 'type': candidate['type'], 'statement': candidate['statement']})
	matching_similarity_queue = sorted(matching_similarity_queue, key = lambda j: j['score'], reverse=True)

	context_distances_queue = []
	for counter, candidate in enumerate(candidates_with_scores):
		context_distances_queue.append({'id': counter, 'candidate': candidate[candidate['type']], 'score': candidate['score']['context_relevance'], 'statement': candidate['statement'] })
	context_distances_queue = sorted(context_distances_queue, key = lambda j: j['score'], reverse=True)

	kg_priors_queue = []
	for counter, candidate in enumerate(candidates_with_scores):
		kg_priors_queue.append({'id': counter, 'candidate': candidate[candidate['type']], 'score': candidate['score']['priors'], 'statement': candidate['statement'] })
	kg_priors_queue = sorted(kg_priors_queue, key = lambda j: j['score'], reverse=True)

	top_candidates =  fagins_algorithm(matching_similarity_queue, context_distances_queue, kg_priors_queue, frontier_hyperparameters, k=k)
	return top_candidates

# Evaluation

# print to specified file
def print_results(text):
	with open( "results.txt", "a+") as file:
		try:
			file.write(str(text) + "\n")
		except Exception as e:
			file.write("Exception occured\n")

# print to specified file
def print_temp_results(text):
	with open( "results_temp.txt", "a+") as file:
		try:
			file.write(str(text) + "\n")
		except Exception as e:
			file.write("Exception occured\n")

# fetch the top k best ranked answers from the answer set
def get_top_k_answers_ranked(answers, k=5):
	ranked_answers = []
	answers = sorted(answers, key = lambda j: j['answer_score'], reverse=False)
	last_answer_score = -1
	rank = 0
	same_ranked = 0
	for answer in answers:
		if answer['answer_score'] == last_answer_score:
			ranked_answers.append({'answer': answer['answer'], 'answer_score': answer['answer_score'], 'rank': rank})
			same_ranked += 1
		else:
			rank += (1 + same_ranked)
			# done
			if k and rank > k:
				break
			last_answer_score = answer['answer_score']
			same_ranked = 0
			ranked_answers.append({'answer': answer['answer'], 'answer_score': answer['answer_score'], 'rank': rank})
	return ranked_answers

def MRR_score(answers, golden_answers):
	# check if any answer was given
	if not answers:
		return 0.0
	for answer in answers:
		if answer['answer'] in golden_answers:
			return (1.0/float(answer['rank']))
		elif answer['answer'] in [golden_answer.lower().strip() for golden_answer in golden_answers]:
			return (1.0/float(answer['rank']))
	return 0.0

def precision_at_1(answers, golden_answers):
	# check if any answer was given
	if not answers:
		return 0.0
	for answer in answers:
		if float(answer['rank']) > float(1.0):
			break
		elif answer['answer'] in golden_answers:
			return 1.0
		elif answer['answer'] in [golden_answer.lower().strip() for golden_answer in golden_answers]:
			return 1.0
	return 0.0

def hit_at_5(answers, golden_answers):
	# check if any answer was given
	if not answers:
		return 0.0
	for answer in answers:
		if float(answer['rank']) > float(5.0):
			break
		elif (answer['answer'] in golden_answers):
			return 1.0
		elif answer['answer'] in [golden_answer.lower().strip() for golden_answer in golden_answers]:
			return 1.0
	return 0.0


# Convex

# answer the given question
def answer_complete_question(question, tagmeToken):
	entities = tagme_get_all_entities(question, tagmeToken) 
	highest_matching_similarity = -1
	for entity in entities:
		shortened_question = string.shorten_question_for_predicate_similarity(question, entity['spot'])# Eliminate nonsense words
		statements = wd.get_all_statements_of_entity(entity['wikidata_id'])# Call base_search to query all triples
		for statement in statements:
			# no identifier predicates
			if statement['predicate']['id'] in identifier_predicates:
				continue
			predicate_label 	= wd.wikidata_id_to_label(statement['predicate']['id'])# Return English label
			matching_similarity = spacy.similarity_word2vec(predicate_label, shortened_question) * entity['link_probability']
			# The word vector similarity is calculated
			if highest_matching_similarity == -1 or matching_similarity > highest_matching_similarity:
				answer 		= statement['entity']['id'] if statement['object']['id'] == entity['wikidata_id'] else statement['object']['id']
				context 	= {'entity': {'id': entity['wikidata_id']}, 'predicate': {'id': statement['predicate']['id']}, 'object': {'id': answer}}
				result 		= {'context': context, 'answers': [{'answer': answer, 'rank': 1}] }
				highest_matching_similarity = matching_similarity
	wd.wikidata_id_to_label(result[answers][answer])
	return result

# answer a follow-up question at a given turn with a given context
def answer_follow_up_question(question, turn, graph, hyperparameters, number_of_frontier_nodes):
	question_words = string.create_question_words_list(question)
	# graph: initial context graph
	candidates = build_candidate_queue(graph)
	# The candidates are the points whose similarity in three factors is to be calculated later
	# distance and priors are the same for all question words
	candidates = determine_attributes(candidates, graph, turn) # Relevance to context
	for candidate in candidates:
		candidate['score']['matching_similarity'] = 0
		for question_word in question_words:
			matching_score = determine_matching_similarity(question_word, candidate, is_question_entity=False)
			if matching_score > candidate['score']['matching_similarity']:
				candidate['score']['matching_similarity'] = matching_score

	frontiers = [(frontier['candidate'], frontier['statement'], frontier['score']) for frontier in determine_top_candidates(candidates, hyperparameters[:3], number_of_frontier_nodes)]
	integrated_frontiers = []
	for frontier, frontier_statement, score in frontiers:
		# expand the graph
		graph, frontier = gp.expand_context_with_frontier(graph, frontier, frontier_statement, turn)
		# integrated frontiers to receive exact graph representation of predicate
		integrated_frontiers.append((frontier, frontier_statement, score))

	answer_candidates = gp.get_all_answer_candidates(graph)
	# Candidate answer refers to the node of type entity in the latest context, but does not include QA nodes
	# Include subject entity and object entity
	# The graph here consists of three frontiers and initial contexts
	h4, h5 = hyperparameters[3:5]
	answers = []
	# determine the answer scores
	for answer_candidate in answer_candidates:
		total_distance_frontiers = 0
		# add up distances to all frontiers
		for (frontier, frontier_statement, score) in integrated_frontiers:
			distance = gp.get_distance(graph, answer_candidate, frontier)
			# Calculate the distance between frontier and answer_candidate, and frontier might just be answer_candidate
			total_distance_frontiers +=  distance * float(score)# The score here refers to the score calculated by Fagin's algorithm
		total_distance_frontiers = total_distance_frontiers / float(len(integrated_frontiers) if len(integrated_frontiers) else 1)
		total_distance_qa_nodes = 0
		# add up weighted distance to all qa nodes
		for node in gp.get_all_qa_nodes(graph):
			distance = gp.get_distance(graph, answer_candidate, node[0]) # Distance between answer candidate and q0-(t-1), a0-(t-1)
			total_distance_qa_nodes += distance * (float(1.0/(float(node[1]['turn'])-1.0)) if turn == 1 else float(1.0/(float(turn))))
		total_distance_qa_nodes = total_distance_qa_nodes / float(len(gp.get_all_qa_nodes(graph)))
		total_distance = h4 * total_distance_qa_nodes + h5 * total_distance_frontiers
		answers.append({'answer': answer_candidate, 'answer_score': total_distance})
	ranked_answers = get_top_k_answers_ranked(answers, k=False)
	top_1 = get_top_k_answers_ranked(answers, k=1)	
	gp.set_all_nodes_as_qa_nodes(graph)

	# If the question is general question, the anser is "yes" or "no"
	if question_is_existential(question):
		ranked_answers = [{'answer': "yes", 'answer_score': 1.0, 'rank': 1}, {'answer': "no", 'answer_score': 0.5, 'rank': 2}]
	return ranked_answers, graph

# answer a complete conversation 
def answer_conversation(questions, tagmeToken, hyperparameters, number_of_frontier_nodes):
	answers = []
	result 	= answer_complete_question(questions[0], tagmeToken)
	graph 	= gp.expand_context_with_statements(None, [result['context']], qa=True) 
	answers.append(result['answers'])
	for counter, question in enumerate(questions[1:]):
		turn = counter + 2
		answer, graph 	= answer_follow_up_question(question, turn, graph, hyperparameters, number_of_frontier_nodes)
		answers.append(answer)
	return answers

#####################################################
###		Load data
#####################################################

# open the identifier predicates
with open( "source/old/data/identifier_predicates.json", "r") as data:
	identifier_predicates = json.load(data)

# open the settings
with open( "settings.json", "r") as data:
	settings 					= json.load(data)
	hyperparameters 			= settings['hyperparameters_frontier_detection'] + settings['hyperparameters_answer_detection']
	number_of_frontier_nodes 	= settings['number_of_frontier_nodes']
	tagmeToken 					= settings['tagMe_token']
	domain 						= settings['domain']
	conversations_path			= settings['conversations_path']
	telegram_chat_id			= settings['telegram_chat_id']
	telegram_active 			= isinstance(telegram_chat_id, int)

if __name__ == '__main__':
	# open the conversations
	with open(conversations_path, "r") as data:
		conversations = json.load(data)

	question_counter = 0
	total_mrr_score = 0.0
	total_precision_at_1_score = 0.0
	total_hit_at_5_score = 0.0
	
	for conversation in conversations:
		if domain != "ALL" and (not conversation['domain'] == domain):
			continue
		questions 		= [turn['question'] for turn in conversation['questions']]
		answers 		= answer_conversation(questions, tagmeToken, hyperparameters, number_of_frontier_nodes)
		golden_answers	= [string.parse_answers(turn['answer']) for turn in conversation['questions']]

		for index, answer in enumerate(answers[1:]):
			total_mrr_score				+= MRR_score(answer, golden_answers[1:][index])
			total_precision_at_1_score 	+= precision_at_1(answer, golden_answers[1:][index])
			total_hit_at_5_score 		+= hit_at_5(answer, golden_answers[1:][index])
			question_counter 			+= 1

	print_results("Test")
	print_results( domain )
	print_results( "MRR_score: 	" + str((question_counter, (total_mrr_score/float(question_counter)), total_mrr_score)))
	print_results( "P@1: 		" + str((question_counter, (total_precision_at_1_score/float(question_counter)), total_precision_at_1_score)))
	print_results( "H@5: 		" + str((question_counter, (total_hit_at_5_score/float(question_counter)), total_hit_at_5_score)))
	print_results("\n")

	wd.save_cached_data()
	spacy.save_cached_data()
	


