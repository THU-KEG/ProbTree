import json
import os

def findAllFile(base):
    for root, ds, fs in os.walk(base):
        for f in fs:
            yield f
base = './outputs'
data = []
for file_name in findAllFile(base):
    data += [json.loads(line.strip()) for line in open(os.path.join(base, file_name))]
    # data.update(json.load(open(os.path.join(base, file_name))))
print(len(data))
json.dump(data, open(os.path.join(base, 'predictions.json'), 'w'), indent = 2)