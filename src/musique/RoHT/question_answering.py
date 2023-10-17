from openai_req import OpenaiReq
import requests
import os
from transformers import AutoTokenizer

openai_caller = OpenaiReq()

tokenizer = AutoTokenizer.from_pretrained("gpt2")

def bm25_search(question, k):
    web = "http://127.0.0.1:1435"
    data = {
        "query": question,
        "k": k
    }
    for i in range(3):
        try:
            r = requests.get(web, json=data)
            if r.status_code != 200:
                raise Exception(r.text)
            return r.json()
        except Exception as e:
            print(e)

def postprocess(response):
    response = response[0]
    if response == 'too long' or response['finish_reason'] != 'stop':
        return 'ERROR: prompt too long', -100, ""
    tokens = response['logprobs']['tokens']
    token_logprobs = response['logprobs']['token_logprobs']
    cot = response['text'].strip()
    if len(token_logprobs) == 0:
        return 'ERROR: empty output', -100, cot
    pos = 0
    for idx, token in enumerate(tokens):
        if token.strip() == 'So' and idx + 1 <= len(tokens) and tokens[idx + 1].strip() == 'the' and idx + 2 <= len(tokens) and tokens[idx + 2].strip() == 'answer' and idx + 3 <= len(tokens) and tokens[idx + 3].strip() == 'is' and idx + 4 <= len(tokens) and tokens[idx + 4].strip() == ':':
            pos = idx
            break
    if tokens[-1] == '.':
        answer_logprobs = token_logprobs[pos+5:-1]
        answer = cot.split('So the answer is: ')[-1][:-1]
    else:
        answer_logprobs = token_logprobs[pos+5:]
        answer = cot.split('So the answer is: ')[-1]
    cot_process = cot.split('So the answer is: ')[0].strip()
    cot_process_logprobs = token_logprobs[:pos]
    if len(cot_process_logprobs) == 0:
        cot_process_logprob = -100
    else:
        cot_process_logprob = sum(cot_process_logprobs) / len(cot_process_logprobs)
    return answer, cot_process_logprob, cot

def get_cb_answer(question):
    instruction = '\n'.join([_.strip() for _ in open('cb/prompt.txt').readlines()])
    prompt = instruction + '\nQ: ' + question + '\nA:'
    response, tag = openai_caller.req2openai(prompt=prompt, max_tokens=256, stop='Q:', use_cache=True)
    return postprocess(response)

def get_singlehop_ob_answer(question, topic_entities):
    instruction = '\n'.join([_.strip() for _ in open('ob/singlehop_prompt.txt').readlines()])
    for k in range(5, 0, -1):
        contexts = []
        hist = set()
        r = bm25_search(question, k) 
        for datum in r:
            title, text = datum["title"], datum["paragraph_text"]
            stamp = title + text
            if not stamp in hist:
                hist.add(stamp)
                contexts.append([title, text])
            
        prompt = instruction + '\n'
        for idx, (title, text) in enumerate(contexts):
            prompt += '\n#' + str(idx + 1) + ' Wikipedia Title: ' + title + '\nText: ' + text 
        prompt += '\nQ: ' + question + '\nA:'
        if len(tokenizer(prompt).input_ids) + 256 <= 4097:
            break
    response, tag = openai_caller.req2openai(prompt=prompt, max_tokens=256, stop='\n\n', use_cache=True)
    return postprocess(response)

def aggregate_singlehop_answer(cb_answer, ob_answer):
    cb_ans, cb_score, cb_cot = cb_answer
    ob_ans, ob_score, ob_cot = ob_answer
    if "ERROR" in cb_ans or 'Unknown' in cb_ans:
        cb_ans, cb_score = "", -100
    if "ERROR" in ob_ans or 'Unknown' in ob_ans:
        ob_ans, ob_score = "", -100
    return max([(cb_ans, cb_score, cb_cot), (ob_ans, ob_score, ob_cot)], key=lambda x:x[1])

def get_multihop_ob_answer(node, tree):
    
    def is_descendant(a, b):
        while "fa" in tree[a]:
            a = tree[a]["fa"]
            if a == b:
                return True
        return False
    
    question = node["question"]
    instruction = '\n'.join([_.strip() for _ in open('ob/multihop_prompt.txt').readlines()])
    k = 5
    for sub_k in range(3, 0, -1):
        contexts = []
        hist = set()
        r = bm25_search(question, k)
        for datum in r:
            title, text = datum["title"], datum["paragraph_text"]
            stamp = title + text
            if stamp not in hist:
                hist.add(stamp)
                contexts.append([title, text])

        for idx in range(node["idx"]):
            if is_descendant(idx, node["idx"]):
                sub_question = tree[idx]["question"]
                r = bm25_search(sub_question, sub_k)
                for datum in r:
                    title, text = datum["title"], datum["paragraph_text"]
                    stamp = title + text
                    if stamp not in hist:
                        hist.add(stamp)
                        contexts.append([title, text])
        
        prompt = instruction + '\n'
        for idx, (title, text) in enumerate(contexts):
            prompt += '\n#' + str(idx + 1) + ' Wikipedia Title: ' + title + '\nText: ' + text 
        prompt += '\nQ: ' + question + '\nA: '
        if len(tokenizer(prompt).input_ids) + 256 <= 4097:
            break
    response, tag = openai_caller.req2openai(prompt=prompt, max_tokens=256, stop='\n\n', use_cache=True)
    return postprocess(response)

def calculate_score1(cot_process_logprob, qd_score, sub_answer_scores):
    return cot_process_logprob + qd_score + sum(sub_answer_scores)

def calculate_score2(cot_process_logprob, qd_score, sub_answer_scores):
    return (cot_process_logprob + qd_score + sum(sub_answer_scores)) / (len(sub_answer_scores) + 2)

def aggregate_multihop_answer(node, tree):
    instruction = '\n'.join([_.strip() for _ in open('aggregate/prompt.txt').readlines()])
    question = node["question"]
    qd_score = node["qd_logprob"]
    context = ''
    sub_answer_scores = []
    for son_idx in node["sons"]:
        sub_question = tree[son_idx]["question"]
        sub_answer = tree[son_idx]["answer"][0]
        sub_answer_scores.append(tree[son_idx]["answer"][1])
        context += '\n' + sub_question + ' ' + sub_answer
    prompt = instruction + '\nContext:\n{}\n\nQuestion:\n{}\n\nAnswer:'.format(context, question)
    response, tag = openai_caller.req2openai(prompt=prompt, max_tokens=256, stop='\n\n\n', use_cache=True)
    child_answer, cot_process_logprob, child_cot = postprocess(response)
    
    child_ans = child_answer
    child_score = calculate_score2(cot_process_logprob, qd_score, sub_answer_scores)
    res1 = (child_ans, child_score, child_cot)
    cb_ans, cb_score, cb_cot = node["cb_answer"]
    ob_ans, ob_score, ob_cot = node["ob_answer"]
    if "ERROR" in cb_ans or 'Unknown' in cb_ans:
        cb_ans, cb_score = "", -100
    if "ERROR" in ob_ans or 'Unknown' in ob_ans:
        ob_ans, ob_score = "", -100
    if "ERROR" in child_ans or "Unknow" in child_ans:
        child_ans, child_score = "", -100
    res2 = max([(cb_ans, cb_score, cb_cot), (ob_ans, ob_score, ob_cot), (child_ans, child_score, child_cot)], key=lambda x:x[1])
    return res1, res2
    
        
    
if __name__ == "__main__":
    question = "Which religious order founded Harvard College?"
    r = bm25_search(question, k=5)
    for x in r:
        print(x["title"])
        print(x["paragraph_text"])
        print()
    
    
    

