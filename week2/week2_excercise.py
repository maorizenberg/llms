import os
import json
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr
import base64
from io import BytesIO
from PIL import Image
from pydub import AudioSegment
from pydub.playback import play


load_dotenv(override=True)

openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key:
    print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
else:
    print("OpenAI API Key not set")

MODEL = "gpt-4o-mini"
openai = OpenAI()

system_message = "You are a helpful assistant for an Airline called FlightAI. "
system_message += "Give short, courteous answers, no more than 1 sentence. "
system_message += "Always be accurate. If you don't know the answer, say so."

ticket_prices = {
    "london": "$799",
    "paris": "$899",
    "tokyo": "$1400",
    "berlin": "$499",
    "jerusalem": "$1200",
    "new york": "$999",
    "sydney": "$1500",
    "cairo": "$800",
    "mumbai": "$1300",
    "beijing": "$1100",
}


def get_ticket_price(destination_city):
    print(f"Tool get_ticket_price called for {destination_city}")
    city = destination_city.lower()
    return ticket_prices.get(city, "Unknown")


price_function = {
    "name": "get_ticket_price",
    "description": "Get the price of a return ticket to the destination city. Call this whenever you need to know the ticket price, for example when a customer asks 'How much is a ticket to this city'",
    "parameters": {
        "type": "object",
        "properties": {
            "destination_city": {
                "type": "string",
                "description": "The city that the customer wants to travel to",
            },
        },
        "required": ["destination_city"],
        "additionalProperties": False,
    },
}


def handle_tool_call(message):
    tool_call = message.tool_calls[0]
    tool_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    city = arguments.get("destination_city")

    if tool_name == "get_ticket_price":
        result = get_ticket_price(city)
        payload = {"destination_city": city, "price": result}
    elif tool_name == "book_ticket":
        result = book_ticket(city)
        payload = {"destination_city": city, "booking_status": result}
    else:
        payload = {"error": "Unknown tool"}

    response = {
        "role": "tool",
        "content": json.dumps(payload),
        "tool_call_id": tool_call.id,
    }
    return response, city


def artist(city):
    image_response = openai.images.generate(
        model="dall-e-3",
        prompt=f"An image representing a vacation in {city}, showing tourist spots and everything unique about {city}, in a vibrant pop-art style",
        size="1024x1024",
        n=1,
        response_format="b64_json",
    )
    image_base64 = image_response.data[0].b64_json
    image_data = base64.b64decode(image_base64)
    return Image.open(BytesIO(image_data))


def book_ticket(destination_city):
    print(f"Tool book_ticket called for {destination_city}")
    city = destination_city.lower()
    if city in ticket_prices:
        return f"Your ticket to {city} has been booked successfully."
    else:
        return "Sorry, I couldn't find a ticket for that destination."


book_function = {
    "name": "book_ticket",
    "description": "Book a return flight to the specified city. Use this when a customer asks to book a ticket.",
    "parameters": {
        "type": "object",
        "properties": {
            "destination_city": {
                "type": "string",
                "description": "The city that the customer wants to book a ticket to",
            },
        },
        "required": ["destination_city"],
        "additionalProperties": False,
    },
}

tools = [
    {"type": "function", "function": price_function},
    {"type": "function", "function": book_function},
]


def talker(message):
    response = openai.audio.speech.create(
        model="tts-1",
        voice="onyx",  # Also, try replacing onyx with alloy
        input=message,
    )

    audio_stream = BytesIO(response.content)
    audio = AudioSegment.from_file(audio_stream, format="mp3")
    play(audio)


def chat(history):
    messages = [{"role": "system", "content": system_message}] + history
    response = openai.chat.completions.create(
        model=MODEL, messages=messages, tools=tools
    )
    image = None

    if response.choices[0].finish_reason == "tool_calls":
        message = response.choices[0].message
        response, city = handle_tool_call(message)
        messages.append(message)
        messages.append(response)
        # image = artist(city)
        response = openai.chat.completions.create(model=MODEL, messages=messages)

    reply = response.choices[0].message.content
    history += [{"role": "assistant", "content": reply}]

    # Comment out or delete the next line if you'd rather skip Audio for now..
    talker(reply)

    return history, image


def transcribe_audio(audio_path):
    print(f"Transcribing {audio_path}")
    with open(audio_path, "rb") as audio_file:
        transcript = openai.audio.transcriptions.create(
            model="whisper-1", file=audio_file
        )
    return transcript.text


with gr.Blocks() as ui:
    with gr.Row():
        chatbot = gr.Chatbot(height=500, type="messages")
        image_output = gr.Image(height=500)
    with gr.Row():
        text_entry = gr.Textbox(label="Chat with our AI Assistant:")
        audio_input = gr.Audio(
            sources="microphone", type="filepath", label="Or speak to the Assistant"
        )
    with gr.Row():
        clear = gr.Button("Clear")


    def do_entry(message, audio, history):
        if audio:
            message = transcribe_audio(audio)
        history += [{"role": "user", "content": message}]
        return "", None, history
    
    audio_input.change(
        fn=do_entry,
        inputs=[text_entry, audio_input, chatbot],
        outputs=[text_entry, audio_input, chatbot]
    ).then(
        fn=chat,
        inputs=chatbot,
        outputs=[chatbot, image_output]
    )

    text_entry.submit(
    fn=do_entry,
    inputs=[text_entry, audio_input, chatbot],
    outputs=[text_entry, audio_input, chatbot]
    ).then(
        fn=chat,
        inputs=chatbot,
        outputs=[chatbot, image_output]
    )

    clear.click(lambda: None, inputs=None, outputs=chatbot, queue=False)

ui.launch(inbrowser=True)
