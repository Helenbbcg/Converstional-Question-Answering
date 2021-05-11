import sys
import requests
import pickle as pkl
from tool import wat_entity_linking

"""
SELECT distinct ?subject ?p ?statement ?ps_object
{ VALUES(?subject){(wd:Q5816)}?subject ?p ?statement.?statement ?ps ?ps_object.?wd wikibase:claim ?p. ?wd wikibase:statementProperty ?ps.}
"""
# entity as subject
query_str_subject = "https://query.wikidata.org/sparql?query=SELECT%20distinct%20%3Fsubject%20%3Fp%20%3Fstatement%20%3Fobject%0A%7B%20VALUES(%3Fsubject)%7B(wd%3A"+ "{}" +")%7D%3Fsubject%20%3Fp%20%3Fstatement.%3Fstatement%20%3Fps%20%3Fobject.%3Fwd%20wikibase%3Aclaim%20%3Fp.%20%3Fwd%20wikibase%3AstatementProperty%20%3Fps.%7D&format=json"
# entity as object
# query_str_object = "https://query.wikidata.org/sparql?query=SELECT%20distinct%20%3Fsubject%20%3Fp%20%3Fobject%0A%7B%20VALUES(%3Fobject)%7B(wd%3A" + "{}" + ")%7D%3Fsubject%20%3Fp%20%3Fstatement.%3Fstatement%20%3Fps%20%3Fobject.%3Fwd%20wikibase%3Aclaim%20%3Fp.%20%3Fwd%20wikibase%3AstatementProperty%20%3Fps.%7D%0A"
query_str_object = "https://query.wikidata.org/sparql?query=SELECT%20distinct%20%3Fsubject%20%3Fp%20%3Fobject%0A%7B%20VALUES(%3Fobject)%7B(wd%3A" + "{}" +")%7D%3Fsubject%20%3Fp%20%3Fstatement.%3Fstatement%20%3Fps%20%3Fobject.%3Fwd%20wikibase%3Aclaim%20%3Fp.%20%3Fwd%20wikibase%3AstatementProperty%20%3Fps.%7D%0A&format=json"
# object is statement
query_str_statement = "https://query.wikidata.org/sparql?query=SELECT%20distinct%20%3Fsubject%20%3Fp%20%3Fstatement%0A%7B%20VALUES(%3Fsubject)%7B(wd%3A" + "{}" + ")%7D%3Fsubject%20%3Fp%20%3Fstatement.%3Fstatement%20%3Fps%20%3Fobject.%3Fwd%20wikibase%3Aclaim%20%3Fp.%20%3Fwd%20wikibase%3AstatementProperty%20%3Fps.%7D&format=json"
match_partan = {
            0: [query_str_subject, query_str_statement],
            1: [query_str_object, query_str_statement],
            2: [query_str_statement]
}

"""
When was the first book of the book series The Dwarves published?
"""




def get_all_triples(entity_id, ind):
    all_triplets = []
    for pat in match_partan[ind]:
        response = requests.get(pat.format(entity_id))# Query by the ID of the Entity
        requests.packages.urllib3.disable_warnings()
        results = response.json()  # json format
        for cur__ in results['results']['bindings']:
            #if entity_id not in all_triplets.keys():
                #if (entity_id in cur__['subject']['value']) or (entity_id in cur__['ps_object']['value']):
                    #all_triplets[entity_id] = [cur__['subject']['value'], cur__['p']['value'],cur__['ps_bject']['value']]  # Triples
            #else:
                #if (entity_id in cur__['subject']['value']) or (entity_id in cur__['ps_object']['value']):
                    #all_triplets[entity_id].append([cur__['subject']['value'], cur__['p']['value'], cur__['ps_object']['value']])
            if 'statement' in cur__.keys():
                all_triplets.append([cur__['subject']['value'], cur__['p']['value'], cur__['statement']['value']])  # Triples
            else:
                if (entity_id in cur__['subject']['value']) or (entity_id in cur__['object']['value']):
                    all_triplets.append([cur__['subject']['value'], cur__['p']['value'], cur__['object']['value']])  # Triples

    return all_triplets, len(all_triplets)


res = get_all_triples('Q5816', 0)
print(res)
print('------------------------------------------------- test------------------------------------------------------')



