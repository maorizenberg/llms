import os
from dotenv import load_dotenv
import re
import math
from tqdm import tqdm
from huggingface_hub import login
import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments, set_seed
from peft import LoraConfig, PeftModel
from datetime import datetime
from datasets import load_dataset

BASE_MODEL = "meta-llama/Meta-Llama-3.1-8B"
FINETUNED_MODEL = f"ed-donner/pricer-2024-09-13_13.04.39"

DATASET_NAME = "ed-donner/pricer-data"
MAX_SEQUENCE_LENGTH = 182
QUANT_4_BIT = True

# Hyperparameters for QLoRA Fine-Tuning

LORA_R = 32
LORA_ALPHA = 64
TARGET_MODULES = ["q_proj", "v_proj", "k_proj", "o_proj"]

load_dotenv(override=True)

hf_token = os.getenv('HF_TOKEN')
login(hf_token, add_to_git_credential=True)

quant_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_quant_type="nf4")

base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    quantization_config=quant_config,
    device_map="auto",
)

fine_tuned_model = PeftModel.from_pretrained(base_model, FINETUNED_MODEL)

dataset = load_dataset(DATASET_NAME)
train = dataset['train']
test = dataset['test']