import json
from tqdm import tqdm
from termcolor import colored
import os

raw_data = json.load(open('outputs/predictions.json'))

data = {}
for item in tqdm(raw_data):
    prompt = item['prompt']
    question = prompt.split('\n')[-2][len('Q: '):].strip()
    print(colored(question, 'red'))
    try:
        qds = item['response']['text'].strip()
        if qds.endswith('.'):
            qds = qds[:-1]
        hqdt = json.loads(qds)
    except:
        hqdt = None
    



    tokens = item['response']['logprobs']['tokens']
    token_logprobs = item['response']['logprobs']['token_logprobs']
    if len(token_logprobs) == 0:
        continue

    if tokens[-1] == '.':
        token_logprobs = token_logprobs[:-1]
    
    st, ed = 0, 0
    pos = 0
    qds = {}
    for sub_question, qd in hqdt.items():
        while pos < len(tokens):
            if "[" in tokens[pos] and ": [\"" in "".join(tokens[max(pos-1, 0): min(pos+2, len(tokens))]):
                st = pos
                break
            pos += 1
        while pos < len(tokens):
            if "]" in tokens[pos] and "\"]" in "".join(tokens[max(pos-1, 0): min(pos+2, len(tokens))]):
                ed = pos
                break
            pos += 1
        assert pos < len(tokens), sub_question
        qd_score = sum(token_logprobs[st:ed+1]) / len(token_logprobs[st:ed+1])
        qds[sub_question] = (qd, qd_score)
        print(colored(sub_question, 'blue'))
        print("".join(tokens[st:ed+1]))
    
    
    data[question] = qds
json.dump(data, open('question_decompositions.json', 'w'), indent = 2)