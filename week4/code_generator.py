import os
import subprocess
from dotenv import load_dotenv
from huggingface_hub import login, InferenceClient
from transformers import AutoTokenizer

load_dotenv(override=True)

hf_token = os.environ['HF_TOKEN']
login(hf_token, add_to_git_credential=True)

MODEL = "HuggingFaceH4/zephyr-7b-beta"

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

python_hard = """# Be careful to support large number sizes

def lcg(seed, a=1664525, c=1013904223, m=2**32):
    value = seed
    while True:
        value = (a * value + c) % m
        yield value
        
def max_subarray_sum(n, seed, min_val, max_val):
    lcg_gen = lcg(seed)
    random_numbers = [next(lcg_gen) % (max_val - min_val + 1) + min_val for _ in range(n)]
    max_sum = float('-inf')
    for i in range(n):
        current_sum = 0
        for j in range(i, n):
            current_sum += random_numbers[j]
            if current_sum > max_sum:
                max_sum = current_sum
    return max_sum

def total_max_subarray_sum(n, initial_seed, min_val, max_val):
    total_sum = 0
    lcg_gen = lcg(initial_seed)
    for _ in range(20):
        seed = next(lcg_gen)
        total_sum += max_subarray_sum(n, seed, min_val, max_val)
    return total_sum

# Parameters
n = 10000         # Number of random numbers
initial_seed = 42 # Initial seed for the LCG
min_val = -10     # Minimum value of random numbers
max_val = 10      # Maximum value of random numbers

# Timing the function
import time
start_time = time.time()
result = total_max_subarray_sum(n, initial_seed, min_val, max_val)
end_time = time.time()

print("Total Maximum Subarray Sum (20 runs):", result)
print("Execution Time: {:.6f} seconds".format(end_time - start_time))
"""

tokenizer = AutoTokenizer.from_pretrained(MODEL)
messages = messages_for(python_hard)
text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

print('Generating C++ code...')
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