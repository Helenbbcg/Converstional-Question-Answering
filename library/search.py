import sys
import requests
import pickle as pkl
from tool import wat_entity_linking

"""
SELECT distinct ?subject ?p ?statement ?ps_object
{ VALUES(?subject){(wd:Q5816)}?subject ?p ?statement.?statement ?ps ?ps_object.?wd wikibase:claim ?p. ?wd wikibase:statementProperty ?ps.}
"""
query_str = "https://query.wikidata.org/sparql?query=SELECT%20distinct%20%3Fsubject%20%3Fp%20%3Fstatement%20%3Fps_object%0A%7B%20VALUES(%3Fsubject)%7B(wd%3A"+ "{}" +")%7D%3Fsubject%20%3Fp%20%3Fstatement.%3Fstatement%20%3Fps%20%3Fps_object.%3Fwd%20wikibase%3Aclaim%20%3Fp.%20%3Fwd%20wikibase%3AstatementProperty%20%3Fps.%7D&format=json"
input_str = ''
talk_hold = []
"""
When was the first book of the book series The Dwarves published?
"""
while input_str != "#":
    input_str = input().strip()  # Who played the joker in The Dark Knight?  Led Zeppelin had how many band members?
    all_entity = []

    annotations = wat_entity_linking(input_str)
    print("annotations:", annotations)
    tagme_ent = {}
    all_triplets = {}
    if annotations:
        tagme_ent['spot'] = []
        for doc in annotations:
            doc['spot'] = input_str[doc["start"]:doc["end"]]
            tagme_ent['spot'].append(
                    (doc['spot'], doc['wiki_title'], str(doc['wiki_id']), doc['rho'], doc['start'], doc['end']))
        print("tagme_ent:", tagme_ent)
        tagme_ent['wikidata'] = []
        for link in tagme_ent['spot']:
            qid = link[0]
            response = requests.get(
                "https://www.wikidata.org/w/api.php?action=wbsearchentities&search=" + qid + "&language=en&limit=20&format=json")
            results = response.json()  # json format
            print('cur results 9999999999999999999:', results)
            entity_id = results['search'][0]['id']
            print(entity_id)
            print(results['search'][0])
            print('*' * 100)
            # Query all triples
            response = requests.get(query_str.format(entity_id))  # Query by the ID of the Entity
            results = response.json()  # json format
            print('all result:', results)
            for cur__ in results['results']['bindings']:
                print(cur__)
                if entity_id not in all_triplets.keys():
                    if (entity_id in cur__['subject']['value']) or (entity_id in cur__['ps_object']['value']):
                        all_triplets[entity_id] = [cur__['subject']['value'], cur__['p']['value'], cur__['ps_object']['value']]  # Triples
                        all_triplets[entity_id] = [cur__['subject']['value'], cur__['statement']['value'], "MyEntity"]  # Triples
                else:
                    if (entity_id in cur__['subject']['value']) or (entity_id in cur__['ps_object']['value']):
                        all_triplets[entity_id].append([cur__['subject']['value'], cur__['p']['value'], cur__['ps_object']['value']])  # Triples
                        all_triplets[entity_id].append([cur__['subject']['value'], cur__['statement']['value'], "MyEntity"])  # Triples

        pkl.dump(all_triplets, open('triplsts_search_result/' + input_str + ".json", mode='wb'))
        found = False
        for cur_sub, cur_ob in zip(all_triplets.keys(), all_triplets.values()):
            # Iterate through all triples：Form：{Entity1：[<e1, r1, e2>, <e3, r2, e4>, ...], Entity2：[<e1, r1, e2>, <e3, r2, e4>, ...]}
            if found:
                break
            # entity, trip;ets of <sub, prop, ob>
            for cur_sub_1, cur_ob_1 in zip(all_triplets.keys(), all_triplets.values()):
                if found:
                    break
                if cur_sub != cur_sub_1 or cur_sub == cur_sub_1:  # Make sure you compare triples from two different entities, and each entity will have many triples
                    for trips in cur_ob:  # The set of all related triples corresponding to the outermost entity is traversed
                        if found:
                            break
                        for cur_trip in cur_ob_1:  # The set of all related triples corresponding to the innermost entity is traversed
                            if len(trips) == len(cur_trip) == 3:  # Ensure that the saved triples are complete
                                sub_, p_, ob_ = trips[:]
                                sub_1, p_1, ob_1 = cur_trip[:]
                                if sub_.__eq__(ob_1) and ob_.__eq__('MyEntity'):  # The subject of the current triple is the object of another triple

                                    print("Answer link:", p_)
                                    print('*' * 100)
                                    response = requests.get(p_)  # reuqest statement
                                    results = response.json()  # json format
                                    print("results:", results)  # request result
                                    if "played" in input_str:
                                        print('searched entity id:', ob_1.split('/')[-1])
                                        cur_res = results['entities'][ob_1.split('/')[-1]]['claims']['P175']
                                        _answer = [cur_res[0]['mainsnak']['datavalue']['value']['id'],
                                                   cur_res[1]['mainsnak']['datavalue']['value']['id'],
                                                   cur_res[2]['mainsnak']['datavalue']['value']['id'],
                                                        ]
                                        # print('Top three answer id:', top_3_answer)
                                        final_answer = []
                                        print('answer:\t')
                                        for cur_in in _answer:
                                            response = requests.get('http://www.wikidata.org/entity/' + cur_in)
                                            results = response.json()  # json format
                                            final_answer.append('\t' + results['entities'][cur_in]['labels']['lb']['value'])  # The Dark Knight
                                        print(final_answer[-1])
                                    found = True
                                    break











