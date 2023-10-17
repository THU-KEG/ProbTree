import json
from collections import defaultdict
trees = json.load(open("./results/test_k=5_singlehop_serpapi_multiobprompt_oner_best.json", "r"))
cnt = defaultdict(int)
total = 0
for tree in trees:
    for node in tree:
        if "child_answer" in node:
            if node["answer"][1] == node["cb_answer"][1]:
                cnt["non_leaf_cb"] += 1
            elif node["answer"][1] == node["ob_answer"][1]:
                cnt["non_leaf_ob"] += 1
            else:
                cnt["non_leaf_ca"] += 1
        else:
            if node["answer"][1] == node["cb_answer"][1]:
                cnt["leaf_cb"] += 1
            else:
                cnt["leaf_ob"] += 1
        total += 1
        
print(cnt)
keys = ["leaf_ob", "leaf_cb"]
print("leaf_cb: ", cnt["leaf_cb"], cnt["leaf_cb"] / (cnt["leaf_ob"] + cnt["leaf_cb"]))
print("leaf_ob: ", cnt["leaf_ob"], cnt["leaf_ob"] / (cnt["leaf_ob"] + cnt["leaf_cb"]))

print("non_leaf_cb:", cnt["non_leaf_cb"], cnt["non_leaf_cb"] / (cnt["non_leaf_ob"] + cnt["non_leaf_cb"] + cnt["non_leaf_ca"]))
print("non_leaf_ob:", cnt["non_leaf_ob"], cnt["non_leaf_ob"] / (cnt["non_leaf_ob"] + cnt["non_leaf_cb"] + cnt["non_leaf_ca"]))
print("non_leaf_ca:", cnt["non_leaf_ca"], cnt["non_leaf_ca"] / (cnt["non_leaf_ob"] + cnt["non_leaf_cb"] + cnt["non_leaf_ca"]))
