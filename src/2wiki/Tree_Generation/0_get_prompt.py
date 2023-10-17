import json, jsonlines

instruction = '\n'.join([_.strip() for _ in open('prompt.txt').readlines()])

raw_data = jsonlines.open("../../released_data/2wikimultihopqa__v2_test_random_500.jsonl", "r")

prompts = []
for item in raw_data:
    question = item["question_text"]
    prompt = instruction + '\nQ: ' + question + '\nA: '
    prompts.append(prompt)

json.dump(prompts, open('prompts.json', 'w'), indent = 2)
print(len(prompts))