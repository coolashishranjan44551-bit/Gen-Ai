import requests
import os
import json

API=os.getenv("HUGGINGFACEHUB_API_TOKEN")
url="https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
payload={"inputs":"You are a helpful assistant.\nQ: MSSQL deadlock quick checklist?\nA:",
         "parameters":{"max_new_tokens":180,"temperature":0.2}}
r=requests.post(url, headers={"Authorization": f"Bearer {API}"}, json=payload, timeout=120)
print(json.dumps(r.json(), indent=2))
