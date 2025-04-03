import requests
from bs4 import BeautifulSoup
from rich.console import Console
from rich.markdown import Markdown
import ollama

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}


class Website:

    def __init__(self, url):
        """
        Create this Website object from the given url using the BeautifulSoup library
        """
        self.url = url
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")
        self.title = soup.title.string if soup.title else "No title found"
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        self.text = soup.body.get_text(separator="\n", strip=True)


def generate_user_prompt(website_title: str, website_text: str) -> str:
    user_prompt = f"You are looking at a website titled {website_title}"
    user_prompt += "\nThe contents of this website is as follows; \
please provide a short summary of this website in markdown. \
If it includes news or announcements, then summarize these too.\n\n"
    user_prompt += website_text
    return user_prompt


def display_summary(url):
    print(f'Scarping {url}')
    website = Website(url)
    system_prompt = "You are an assistant that analyzes the contents of a website \
        and provides a short summary, ignoring text that might be navigation related. \
        Respond in markdown."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": generate_user_prompt(website.title, website.text)},
    ]
    print('Getting summary')
    response = ollama.chat(model="llama3.2", messages=messages)
    summary = response["message"]["content"]
    console = Console()
    console.print(Markdown(summary))


display_summary("https://imdb.com")
