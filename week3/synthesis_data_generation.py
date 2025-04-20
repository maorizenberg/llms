import os
from huggingface_hub import login
import torch

from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from dotenv import load_dotenv

load_dotenv(override=True)
hf_token = os.getenv("HF_TOKEN")
login(hf_token, add_to_git_credential=True)

MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

messages = [
    {"role": "system", "content": "You are a helpful assistant that generates synthetic structured data. Avoid return special tokens like <|system|> and <|assistant|>"},
    {
        "role": "user",
        "content": (
            "Generate 5 examples of synthetic patient medical records in JSON format. "
            "Each record should include fields: patient_id, age, gender, diagnosis, medications, "
            "vital_signs (with temperature, blood_pressure, heart_rate), and visit_date."
        ),
    },
]

# Quantization Config - this allows us to load the model into memory and use less memory
quant_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_quant_type="nf4",
)

print()
tokenizer = AutoTokenizer.from_pretrained(MODEL,  trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token
inputs = tokenizer.apply_chat_template(messages, return_tensors="pt").to("cuda")

model = AutoModelForCausalLM.from_pretrained(
    MODEL, device_map="auto", quantization_config=quant_config,  trust_remote_code=True
)

outputs = model.generate(inputs, max_new_tokens=512)
decoded_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(decoded_output)


del inputs, outputs, model
torch.cuda.empty_cache()
