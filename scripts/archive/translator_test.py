from dotenv import load_dotenv
import os
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)

def translate_text(text, source_lang, target_lang):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a translator. Translate the following {source_lang} text to {target_lang}."
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Translation error: {str(e)}"

def chunk_text(text, max_chunk_size=4000):
    words = text.split()
    chunks = []
    current_chunk = []

    for word in words:
        if len(" ".join(current_chunk)) + len(word) < max_chunk_size:
            current_chunk.append(word)
        else:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

def translate_large_text(text, source_lang, target_lang):
    chunks = chunk_text(text)
    translated_chunks = []

    for chunk in chunks:
        translated_chunk = translate_text(chunk, source_lang, target_lang)
        translated_chunks.append(translated_chunk)

    return " ".join(translated_chunks)
