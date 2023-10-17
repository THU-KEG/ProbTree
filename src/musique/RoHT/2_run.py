import json
import re
import os
from question_answering import *
from tqdm import tqdm
from parallel import parallel_process_data

PROC_NUM = 50
cnt = 0

def solve(tree):
    global cnt
    cnt += 1
    print(cnt)
    #print(tree[-1])
    try:
        for node in tree:
            #print(node)
            question = node["question_text"].strip()
            ref_tokens = re.findall(r"#\d+", question)
            topic_entities = []
            for ref_token in ref_tokens:
                if "fa" in node and int(ref_token[1:]) <= len(tree[node["fa"]]["sons"]):
                    ref_idx = tree[node["fa"]]["sons"][int(ref_token[1:])-1]
                    if "answer" in tree[ref_idx]:
                        question = question.replace(ref_token, tree[ref_idx]["answer"][0])
                        topic_entities.append(tree[ref_idx]["answer"][0])
            node["question"] = question
            node["cb_answer"] = get_cb_answer(question)
            #print(node["cb_answer"])
            if len(node["sons"]) == 0:
                node["ob_answer"] = get_singlehop_ob_answer(question, topic_entities)
                #print(node["ob_answer"])
                node["answer"] = aggregate_singlehop_answer(node["cb_answer"], node["ob_answer"])
            else:
                node["ob_answer"] = get_multihop_ob_answer(node, tree)
                #print(node["ob_answer"])
                node["child_answer"], node["answer"] = aggregate_multihop_answer(node, tree)
            #print(node)
    except Exception as e:
        print("ERROR CASE")
        print(tree[-1])
        raise e


trees = json.load(open("trees.json", "r"))
print("Total: %d | Start Processing..."%len(trees))
parallel_process_data(trees, solve, PROC_NUM)


print("END")
os.makedirs("results", exist_ok=True)
json.dump(trees, open("results/test.json", "w"), indent=2)