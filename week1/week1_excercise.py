import os
from rich.console import Console
from rich.markdown import Markdown
import ollama
from openai import OpenAI
from dotenv import load_dotenv

MODEL_GPT = 'gpt-4o-mini'
MODEL_LLAMA = 'llama3.2'

load_dotenv(override=True)
api_key = os.getenv('OPENAI_API_KEY')

if api_key and api_key.startswith('sk-proj-') and len(api_key)>10:
    print("API key looks good so far")
else:
    print("There might be a problem with your API key? Please visit the troubleshooting notebook!")

openai = OpenAI()


# Get gpt-4o-mini to answer, with streaming
# Get Llama 3.2 to answer

def explain_question(code_snippet: str):
    user_prompt='Please explain what this code does and why:\n'
    user_prompt += code_snippet

    system_prompt = "You are an expert software enginner that is able to explain every code snippet given to you."
    messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
      ]
    print(f'Asking model {MODEL_GPT}')
    response = openai.chat.completions.create(
        model=MODEL_GPT,
        messages=messages,
    )
    print(f'Answer of model {MODEL_GPT}')
    result = response.choices[0].message.content
    console = Console()
    console.print(Markdown(result))

    print(f'Asking model {MODEL_LLAMA}')
    response = ollama.chat(model="llama3.2", messages=messages)
    print(f'Answer of model {MODEL_LLAMA}')
    result = response["message"]["content"]
    console = Console()
    console.print(Markdown(result))


code_snippet = """
yield from {book.get("author") for book in books if book.get("author")}
"""

explain_question(code_snippet)