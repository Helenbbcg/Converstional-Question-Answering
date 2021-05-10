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
    # for cur_str in input_str.split():
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
            entity_id = results['search'][0]['id']  # 得到QID，你给我的文件运行不了，方法换成这个。
            print(entity_id)
            print(results['search'][0])
            print('*' * 100)
            # 查询所有的三元组
            response = requests.get(query_str.format(entity_id))  # 通过entity的ID进行查询
            results = response.json()  # json format
            print('all result:', results)
            for cur__ in results['results']['bindings']:
                print(cur__)
                if entity_id not in all_triplets.keys():
                    if (entity_id in cur__['subject']['value']) or (entity_id in cur__['ps_object']['value']):
                        all_triplets[entity_id] = [cur__['subject']['value'], cur__['p']['value'], cur__['ps_object']['value']]  # 三元组
                        all_triplets[entity_id] = [cur__['subject']['value'], cur__['statement']['value'], "MyEntity"]  # 三元组
                else:
                    if (entity_id in cur__['subject']['value']) or (entity_id in cur__['ps_object']['value']):
                        all_triplets[entity_id].append([cur__['subject']['value'], cur__['p']['value'], cur__['ps_object']['value']])  # 三元组
                        all_triplets[entity_id].append([cur__['subject']['value'], cur__['statement']['value'], "MyEntity"])  # 三元组
                # subject = requests.get(cur__['subject']['value']).json()
                # print('subject:', subject)
                # p = requests.get(cur__['p']['value'])
                # # print('prop:', p)
                # ps_object = requests.get(cur__['ps_object']['value']).json()
                # print('object:', ps_object)
                # print('*' * 100)
        # 得到所有的三元祖，元祖里面的每一个元素都是一个链接
        # 保存本地
        pkl.dump(all_triplets, open('triplsts_search_result/' + input_str + ".json", mode='wb'))
        # 链接查询
        found = False
        for cur_sub, cur_ob in zip(all_triplets.keys(), all_triplets.values()):
            # 遍历所有的三元组：格式：{实体1：[<e1, r1, e2>, <e3, r2, e4>, ...], 实体2：[<e1, r1, e2>, <e3, r2, e4>, ...]}
            if found:
                break
            # entity, trip;ets of <sub, prop, ob>
            for cur_sub_1, cur_ob_1 in zip(all_triplets.keys(), all_triplets.values()):  # 同上
                if found:
                    break
                if cur_sub != cur_sub_1 or cur_sub == cur_sub_1:  # 保证比较的三元组来自不同的两个实体，每个实体都会有很多个三元组
                    for trips in cur_ob:  # 遍历最外层实体对应的所有相关三元组集合
                        if found:
                            break
                        for cur_trip in cur_ob_1:  # 遍历最内层实体对应的所有相关三元组集合
                            if len(trips) == len(cur_trip) == 3:  # 保证保存的三元组是完整的
                                sub_, p_, ob_ = trips[:]
                                sub_1, p_1, ob_1 = cur_trip[:]
                                if sub_.__eq__(ob_1) and ob_.__eq__('MyEntity'):  # 当前三元组的主体是另外一个三元组的客体
                                    # response = requests.get(ob_1)  # 查询客体，其实不用查
                                    # results = response.json()  # json format
                                    # print('客体的查询:', results)
                                    print("Answer link:", p_)
                                    print('*' * 100)
                                    response = requests.get(p_)  # 请求 statement
                                    results = response.json()  # json format
                                    print("results:", results)  # 请求结果
                                    # print("results:", results['entities']['Q217533'])
                                    # if "played" in input_str:
                                    # talk_hold.append("Q40572")
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











