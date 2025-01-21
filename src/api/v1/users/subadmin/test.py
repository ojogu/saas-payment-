import os
import json

print(os.getcwd())
script_dir=os.path.dirname(os.path.abspath(__file__))

file_path=os.path.join(script_dir,'banks.json')

f=open(file_path,'r')
content=f.read()

data = (json.loads(content))
for i in data:
    for j in data[i]:
        print(j)