import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from openai import OpenAI, OpenAIError
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Get model from .env file
OPENAI_MODEL = os.getenv("OPENAI_MODEL")

def translate_text(text, source_lang, target_lang):
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": f"You are a translator. Translate the following text from {source_lang} to {target_lang}."},
                {"role": "user", "content": text}
            ]
        )
        translated_text = response.choices[0].message.content
        time.sleep(0.1)  # Add a 0.1-second delay after each API call
        return translated_text
    except OpenAIError as e:
        logger.error(f"OpenAI API error: {e}")
        return text  # Return original text if translation fails

def should_translate(tag):
    """Determine if a tag's content should be translated"""
    return tag.name in ['p', 'title', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'th']

def remove_inline_tags(tag):
    """Remove inline tags from within a tag, preserving only the text content"""
    text_content = ''.join(tag.stripped_strings)
    tag.clear()
    tag.append(text_content)

def translate_content(tag, source_lang, target_lang):
    """Remove inline tags, translate the content, and replace the tag's content"""
    remove_inline_tags(tag)
    if tag.string and tag.string.strip():
        translated_text = translate_text(tag.string.strip(), source_lang, target_lang)
        tag.string.replace_with(translated_text)

def translate_table(table, source_lang, target_lang):
    """Translate table name and column headers, but skip rows"""
    if table.get('summary'):
        table['summary'] = translate_text(table['summary'], source_lang, target_lang)
    
    for th in table.find_all('th'):
        translate_content(th, source_lang, target_lang)

def translate_html(soup, source_lang, target_lang):
    """Translate the content of appropriate tags and handle tables specially"""
    for tag in soup.find_all(should_translate):
        if tag.name != 'th':  # Skip 'th' tags as they'll be handled in translate_table
            translate_content(tag, source_lang, target_lang)
    
    for table in soup.find_all('table'):
        translate_table(table, source_lang, target_lang)
    
    for img in soup.find_all('img', alt=True):
        if img['alt'].strip():
            img['alt'] = translate_text(img['alt'], source_lang, target_lang)

def process_file(input_file, source_lang, target_lang):
    logger.info(f"Processing file: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, 'html.parser')
    translate_html(soup, source_lang, target_lang)

    html_tag = soup.find('html')
    if html_tag:
        html_tag['lang'] = target_lang

    with open(input_file, 'w', encoding='utf-8') as file:
        file.write(str(soup))

    logger.info(f"Translated: {input_file}")

def main(input_path, source_lang='en', target_lang='es'):
    input_path = Path(input_path)
    
    if input_path.is_file():
        if input_path.suffix.lower() == '.html':
            process_file(input_path, source_lang, target_lang)
        else:
            logger.error(f"Error: The file '{input_path}' is not an HTML file.")
    elif input_path.is_dir():
        for file in input_path.glob('*.html'):
            process_file(file, source_lang, target_lang)
    else:
        logger.error(f"Error: The path '{input_path}' is neither a file nor a directory.")

    logger.info("Translation complete.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python translate_simple.py <input_path> [source_lang] [target_lang]")
        sys.exit(1)

    input_path = sys.argv[1]
    source_lang = sys.argv[2] if len(sys.argv) > 2 else 'en'
    target_lang = sys.argv[3] if len(sys.argv) > 3 else 'es'

    main(input_path, source_lang, target_lang)
