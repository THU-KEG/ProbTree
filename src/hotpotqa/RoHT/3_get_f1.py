import json

import json
from tqdm import tqdm
from termcolor import colored
from evaluate import update_answer
import math


q2a = {}
raw_data = [json.loads(line.strip()) for line in open('../../../released_data/hotpotqa__v2_test_random_500.jsonl')]
q2dq = json.load(open("../Tree_Generation/question_decompositions.json"))
q2gold = {}
for item in raw_data:
    question = item['question_text'].strip()
    question = list(q2dq[question].keys())[0]
    gold = item['answers_objects'][0]['spans'][0]
    q_type = item["type"]
    q2gold[question] = (gold, q_type)

trees = json.load(open("results/test.json", "r"))
metrics = {}
for q_type in ["all", "bridge", "comparison"]:
    metrics[q_type] = {'em': 0, 'f1': 0, 'prec': 0, 'recall': 0, 'N': 0}

print(len(trees))
for i, tree in enumerate(trees):
    node = tree[-1]
    question, answer = node["question"], node["answer"][0]
    gold, q_type = q2gold[question]
    q2a[question] = (i, answer, gold)
    em, f1, prec, recall = update_answer(metrics["all"], answer, gold)
    update_answer(metrics[q_type], answer, gold)

for q_type in ["all", "bridge", "comparison"]:
    print(q_type)
    print(metrics[q_type]['N'])

    for k in metrics[q_type].keys():
        metrics[q_type][k] /= metrics[q_type]['N']
    print(metrics[q_type])


json.dump(q2a, open("q2a.json", "w"), indent=2)