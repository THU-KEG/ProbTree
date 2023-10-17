import json

import json
from tqdm import tqdm
from termcolor import colored
from evaluate import update_answer
import math


q2a = {}
raw_data = [json.loads(line.strip()) for line in open('../../../released_data/musique_ans__v2_test_random_500.jsonl')]
q2dq = json.load(open("../Tree_Generation/question_decompositions.json"))
q2gold = {}
for item in raw_data:
    question = item['question_text'].strip()
    question = list(q2dq[question].keys())[0]
    gold = item['answers_objects'][0]['spans'][0]
    q_type = item["question_id"].split("hop")[0]+"hop"
    q2gold[question] = (gold, q_type)

trees = json.load(open("./results/test.json", "r"))
metrics = {}
for q_type in ["all", "2hop", "3hop", "4hop"]:
    metrics[q_type] = {'em': 0, 'f1': 0, 'prec': 0, 'recall': 0, 'N': 0}

print(len(trees))
for i, tree in enumerate(trees):
    node = tree[-1]
    question, answer = node["question"], node["answer"][0]
    q2a[question] = answer
    gold, q_type = q2gold[question]
    em, f1, prec, recall = update_answer(metrics["all"], answer, gold)
    update_answer(metrics[q_type], answer, gold)
    if f1 == 0:
        print(colored(question, 'red'))
        print(colored(gold, 'blue'))
        print(answer)

for q_type in ["all", "2hop", "3hop", "4hop"]:
    print(q_type)
    print(metrics[q_type]['N'])

    for k in metrics[q_type].keys():
        metrics[q_type][k] /= metrics[q_type]['N']
    print(metrics[q_type])


json.dump(q2a, open("q2a.json", "w"), indent=2)