import json, jsonlines
from itertools import chain
from tqdm import tqdm

train = jsonlines.open("/data/zjj/LLMReasoning/data/musique/musique_ans_v1.0_train.jsonl", "r")
dev = jsonlines.open("/data/zjj/LLMReasoning/data/musique/musique_ans_v1.0_dev.jsonl", "r")

question = "What genre is the record label of the performer of So Long, See You Tomorrow associated with?"

for item in tqdm(chain(train, dev)):
    if item["question"] != question: continue
    pos_para, neg_para = [], []
    for para in item['paragraphs']:
        if para["is_supporting"]:
            pos_para.append([para["title"], para["paragraph_text"]])
        else:
            neg_para.append([para["title"], para["paragraph_text"]])
    break

print("pos_para:")
for title, para in pos_para:
    print(title)
    print(para)
    print('\n')
exit()
print("neg_para:")
for title, para in neg_para:
    print(title)
    print(para)
    print('\n')