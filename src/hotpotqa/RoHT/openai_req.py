import openai
import requests
import time
import os
import json, jsonlines

class OpenaiReq():
    def __init__(self):
        self.url = "http://127.0.0.1:10001/api/openai/completion"
        self.cache = {}
        self.cache_path = "./cache.jsonl"
        if os.path.exists(self.cache_path):
            with open(self.cache_path, "r") as f:
                for i, line in enumerate(f):
                    #print(i+1)
                    datum = json.loads(line.strip())
                    self.cache[tuple(datum["input"])] = datum["response"]
                f.close()
    
    def req2openai(self, prompt, model="text-davinci-003", temperature=0, max_tokens=128, stop=None, logprobs=1, use_cache=True):
        assert isinstance(prompt, str)
        input = (prompt, model, max_tokens, stop, logprobs)
        if use_cache and temperature == 0 and input in self.cache:
            return self.cache[input], True
        for i in range(3):
            try:
                response = requests.post(self.url, json = {
                    "model": model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stop": stop,
                    "logprobs": logprobs,
                })
                if response.status_code != 200:
                    raise Exception(response.text)
                break
            except Exception as e:
                err_msg = str(e)
                print(e)
                if "reduce your prompt" in err_msg: # this is because the input string too long
                    return ['too long'], False
        try:
            response = response.json()['choices']
        except:
            return ['openai error'], False
        if temperature == 0:
            input = (prompt, model, max_tokens, stop, logprobs)
            res = response[0]
            if input not in self.cache:
                self.cache[input] = [res]
                with open(self.cache_path, "a") as f:
                    f.write("%s\n"%json.dumps({"input": input, "response": [res]}))
                    f.close()
        return response, True

if __name__ == "__main__":
    caller = OpenaiReq()
    res = caller.req2openai("你好", use_cache=True)
    print(res)
    
    