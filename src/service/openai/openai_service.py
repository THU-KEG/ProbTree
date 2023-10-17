import openai, json, os, sys
from flask import Flask, request, jsonify, abort
from datetime import datetime, timedelta, timezone
import openai.error

app = Flask(__name__)

key_pool = [
    #put your keys here
]


print(*key_pool,sep="\n")

class Log:
    @staticmethod
    def time_str():
        current = datetime.now(timezone(timedelta(hours=8)))
        return current.strftime("%Y-%m-%d %H:%M:%S")
    
    @staticmethod
    def log(file_name, log_type, content):
        content = "[%s] %s | %s"%(log_type, Log.time_str(), str(content).replace("\n", "\n    "))
        with open(file_name, "a") as f:
            f.write("%s\n"%content)
    
    @staticmethod
    def message(file_name, content):
        return Log.log( file_name, "MSG",content)
    
    @staticmethod
    def error(file_name, content):
        return Log.log(file_name,"ERR",  content)
    
    @staticmethod
    def warning(file_name, content):
        return Log.log(file_name, "WRN", content)


#  You exceeded your current quota

current_key = 0
def next_key():
    global current_key
    current_key += 1
    current_key %= len(key_pool)
    return key_pool[current_key]

from collections import deque
from datetime import datetime, timedelta
import threading

# Deque to store request timestamps
timestamps = deque()

# Lock for thread safety
lock = threading.Lock()
def update_speed():
    now = datetime.now()
    with lock:
        timestamps.append(now)
        # Remove timestamps older than 5 seconds
        while timestamps and now - timestamps[0] > timedelta(seconds=5):
            timestamps.popleft()
        # Calculate the average request rate
        rate = len(timestamps) / 5
        print("Current request rate in the latest 5 seconds:", rate, "req/s")

@app.route('/api/openai/freq', methods = ["GET"])
def frep():
    now = datetime.now()
    with lock:
        while timestamps and now - timestamps[0] > timedelta(seconds=5):
            timestamps.popleft()
    return jsonify({
        "message": "This is the request rate (requests/second) in the latest 5 seconds.",
        "request_rate": len(timestamps) / 5,
        "availabel_keys": len(key_pool)
    })

@app.route('/api/openai/chat-completion', methods = ["POST"])
def openai_chat_completion():
    key = next_key()
    tt = datetime.now(timezone(timedelta(hours=8)))
    day = tt.strftime("%Y-%m-%d")
    hour = tt.strftime("%H")
    log_dir = "log/%s/%s"%(day, hour)
    log_msg_path = os.path.join(log_dir, "chat-completion.log")
    log_data_path = os.path.join(log_dir, "chat-completion.jsonl")
    os.makedirs(log_dir, exist_ok=True)
    try:
        resp = openai.ChatCompletion.create(**request.json, api_key=key, timeout=20)
    except openai.error.OpenAIError as e:
        Log.error(log_msg_path, str(e))
        print("[Error] %s"%(str(e)))
        if str(e).find("You exceeded your current quota") != -1 or str(e).find("deactivate") != -1:
            key_pool.remove(key)
            Log.error("log/exceed.log", key)
        return abort(500, str(e))
    except Exception as e:
        Log.error(log_msg_path, str(e))
        print("[Error] %s"%(str(e)))
        return abort(500, str(e))
    Log.message(log_msg_path, "Successful")
    with open(log_data_path, "a+") as f:
        f.write("%s\n"%(json.dumps({
            "request": request.json,
            "response": resp
        })))
    update_speed()
    return jsonify(resp)

@app.route('/api/openai/completion', methods = ["POST"])
def openai_completion():
    key = next_key()
    tt = datetime.now(timezone(timedelta(hours=8)))
    day = tt.strftime("%Y-%m-%d")
    hour = tt.strftime("%H")
    log_dir = "log/%s/%s"%(day, hour)
    log_msg_path = os.path.join(log_dir, "completion.log")
    log_data_path = os.path.join(log_dir, "completion.jsonl")
    os.makedirs(log_dir, exist_ok=True)
    try:
        resp = openai.Completion.create(**request.json, api_key=key, timeout=20)
    except openai.error.OpenAIError as e:
        Log.error(log_msg_path, str(e))
        print("[Error] %s"%(str(e)))
        if str(e).find("You exceeded your current quota") != -1 or str(e).find("deactivate") != -1:
            key_pool.remove(key)
            Log.error("log/exceed.log", key)
        return abort(500, str(e))
    except Exception as e:
        Log.error(log_msg_path, str(e))
        print("[Error] %s"%(str(e)))
        return abort(500, str(e))
    Log.message(log_msg_path, "Succeesful")
    with open(log_data_path, "a+") as f:
        f.write("%s\n"%(json.dumps({
            "request": request.json,
            "response": resp
        })))
    update_speed()    
    return jsonify(resp)

if __name__ == '__main__':
    app.run("0.0.0.0", port=10001)
