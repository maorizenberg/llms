import os
import subprocess
from dotenv import load_dotenv
from huggingface_hub import login, InferenceClient
from transformers import AutoTokenizer

load_dotenv(override=True)

hf_token = os.environ['HF_TOKEN']
login(hf_token, add_to_git_credential=True)

MODEL = "meta-llama/Llama-2-7b-chat-hf"

system_message = "You are an assistant that reimplements Python code in high performance C++ for an Intel i7 CPU. "
system_message += "Respond only with C++ code; use comments sparingly and do not provide any explanation other than occasional comments. "
system_message += "The C++ response needs to produce an identical output in the fastest possible time. Keep implementations of random number generators identical so that results match exactly."

def user_prompt_for(python):
    user_prompt = "Rewrite this Python code in C++ with the fastest possible implementation that produces identical output in the least time. "
    user_prompt += "Respond only with C++ code; do not explain your work other than a few comments. "
    user_prompt += "Pay attention to number types to ensure no int overflows. Remember to #include all necessary C++ packages such as iomanip.\n\n"
    user_prompt += python
    return user_prompt

def messages_for(python):
    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_prompt_for(python)}
    ]


pi = """
import time

def calculate(iterations, param1, param2):
    result = 1.0
    for i in range(1, iterations+1):
        j = i * param1 - param2
        result -= (1/j)
        j = i * param1 + param2
        result += (1/j)
    return result

start_time = time.time()
result = calculate(100_000_000, 4, 1) * 4
end_time = time.time()

print(f"Result: {result:.12f}")
print(f"Execution Time: {(end_time - start_time):.6f} seconds")
"""

tokenizer = AutoTokenizer.from_pretrained(MODEL)
messages = messages_for(pi)
text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

client = InferenceClient(MODEL, token=hf_token)
stream = client.text_generation(text, stream=True, details=True, max_new_tokens=3000)
reply = ""
for r in stream:
    reply += r.token.text

code = reply.replace("```cpp","").replace("```","")
with open("optimized.cpp", "w", encoding="utf-8") as f:
    f.write(code)
compiler_cmd = ["clang++", "-O3", "-std=c++17", "-march=native", "-o", "optimized", "optimized.cpp"]
try:
    compile_result = subprocess.run(compiler_cmd, check=True, text=True, capture_output=True)
    run_cmd = ["./optimized"]
    run_result = subprocess.run(run_cmd, check=True, text=True, capture_output=True)
    print(run_result.stdout)
except subprocess.CalledProcessError as e:
    print(f"An error occurred:\n{e.stderr}")