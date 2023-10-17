import json

raw_data = json.load(open('question_decompositions.json'))

def check(question):
    if '#1' in question or '#2' in question or '#3' in question or '#4' in question:
        return True
tree = {}
for father in raw_data:
    if check(father):
        continue
    qds = raw_data[father]
    if qds is None:
        continue
    tree[father] = {}
    for question in qds:
        if check(question):
            continue
        if any([x == question for x in qds[question][0]]):
            tree[father][question] = [[], None]
        else:
            tree[father][question] = qds[question]

question_decompositions = {}
for father in tree:
    qds = tree[father]
    for q in qds:
        if q not in question_decompositions:
            question_decompositions[q] = qds[q]
        else:
            if question_decompositions[q] != qds[q]:
                print(question_decompositions[q])
                print(qds[q])
            else:
                print('haha')

json.dump(question_decompositions, open('tree.json', 'w'), indent = 2)

print(len(tree))