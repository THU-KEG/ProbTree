import json, jsonlines

instruction = '\n'.join([_.strip() for _ in open('prompt.txt').readlines()])

raw_data = jsonlines.open("/data/zjj/LLMReasoning/released_data/hotpotqa__v2_test_random_500.jsonl", "r")

prompts = []
for item in raw_data:
    question = item["question_text"].strip()
    prompt = instruction + '\nQ: ' + question + '\nA:'
    prompts.append(prompt)
    # print(prompt)
    # break    

json.dump(prompts, open('prompts.json', 'w'), indent = 2)
print(len(prompts))