import json
from collections import defaultdict

raw_data = [json.loads(line.strip()) for line in open('../../../released_data/2wikimultihopqa__v2_test_random_500.jsonl')]
q2sub_q = json.load(open("../Tree_Generation/tree.json"))

trees = []

def dfs(q, tree):
    sons = []
    print(q)
    for sub_q in q2sub_q.get(q, [[]])[0]:
        son_idx = dfs(sub_q, tree)
        sons.append(son_idx)
    idx = len(tree)
    tree.append({
        "idx": idx,
        "question_text": q,
        "sons": sons,
        "qd_logprob": q2sub_q.get(q, [[], None])[1]
    })    
    for son_idx in sons:
        tree[son_idx]["fa"] = idx
    return idx

for item in raw_data:
    question = item['question_text'].strip()
    assert question in q2sub_q
    tree = []
    dfs(question, tree)
    trees.append(tree)

json.dump(trees, open("trees.json", "w"), indent=2)
    
    
    

