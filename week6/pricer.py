import os
import re
from dotenv import load_dotenv
from huggingface_hub import login
import numpy as np
import pickle
from collections import Counter
from openai import OpenAI

from items import Item

load_dotenv(override=True)

hf_token = os.environ['HF_TOKEN']
login(hf_token, add_to_git_credential=True)

openai = OpenAI()

with open(os.path.join(os.path.dirname(__file__), 'train.pkl'), 'rb') as file:
    train = pickle.load(file)

with open(os.path.join(os.path.dirname(__file__), 'test.pkl'), 'rb') as file:
    test = pickle.load(file)

def messages_for(item):
    system_message = "You estimate prices of items. Reply only with the price, no explanation"
    user_prompt = item.test_prompt().replace(" to the nearest dollar","").replace("\n\nPrice is $","")
    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_prompt},
        {"role": "assistant", "content": "Price is $"}
    ]

def get_price(s):
    s = s.replace('$','').replace(',','')
    match = re.search(r"[-+]?\d*\.\d+|\d+", s)
    return float(match.group()) if match else 0

def gpt_4o_mini(item):
    response = openai.chat.completions.create(
        model="gpt-4o-mini", 
        messages=messages_for(item),
        seed=42,
        max_tokens=5
    )
    reply = response.choices[0].message.content
    return get_price(reply)

print(gpt_4o_mini(test[0]))