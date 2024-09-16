from openai import OpenAI
from lxml import etree
import re
from dotenv import load_dotenv
import os
import time
import uuid
from bs4 import BeautifulSoup
from packages.preprocess import preprocess
import shutil
from io import BytesIO
import tiktoken
from ebooklib import epub

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)


def tokenize_inline_tags(text):
    """
    Tokenize inline XHTML tags and HTML entities for quotes, replacing them with unique placeholders.
    """
    tag_map = {}
    
    def replace_tag_or_entity(match):
        token = f"__TOKEN_{uuid.uuid4()}__"
        tag_map[token] = match.group(0)
        return token
    
    # Pattern for inline tags and HTML entities for quotes
    pattern = r'<(u|strong|em|q)>.*?</\1>|&#x201[cd];|&#x2018;|&#x2019;'
    tokenized_text = re.sub(pattern, replace_tag_or_entity, text, flags=re.DOTALL)
    
    return tokenized_text, tag_map

def detokenize_inline_tags(text, tag_map):
    """
    Replace placeholders with their original inline XHTML tags and HTML entities.
    """
    for token, original in tag_map.items():
        text = text.replace(token, original)
    return text

def split_text(text, max_tokens=4096):
    """
    Splits text into chunks based on a maximum token count.
    """
    words = text.split()
    chunks = []
    current_chunk = []
    current_token_count = 0
    
    for word in words:
        word_tokens = len(word) // 4 + 1  # Rough estimate
        if current_token_count + word_tokens > max_tokens:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_token_count = word_tokens
        else:
            current_chunk.append(word)
            current_token_count += word_tokens
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks


def translate_chunk(chunk, source_lang, target_lang, file_name=None, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini", #never change this model!

                messages=[
                    {
                        "role": "system",
                        "content": f"You are a translator. Translate the following {source_lang} text to {target_lang}."
                    },
                    {
                        "role": "user",
                        "content": chunk
                    }
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Translation attempt {attempt + 1} failed: {str(e)}")
                time.sleep(2)  # Wait for 2 seconds before retrying
            else:
                print(f"Translation failed after {max_retries} attempts: {str(e)}")
                return f"[UNTRANSLATED: {chunk}]"  # Mark untranslated text
            
def translate_large_text(text, source_lang, target_lang, file_name=None):
    tokenized_text, tag_map = tokenize_inline_tags(text)
    chunks = split_text(tokenized_text)
    translated_chunks = [translate_chunk(chunk, source_lang, target_lang, file_name) for chunk in chunks]
    translated_text = ' '.join(translated_chunks)
    return detokenize_inline_tags(translated_text, tag_map)

def translate_xhtml(content, filename, source_lang, target_lang):
    """
    Translates the content of an XHTML file, preserving the structure.
    """
    # Parse the XHTML content
    soup = BeautifulSoup(content, 'lxml-xml')

    # Remove span, sup, and sub tags
    for tag in soup.find_all(['span', 'sup', 'sub']):
        tag.unwrap()

    # Extract text content for translation
    text_nodes = soup.find_all(string=True)
    
    # Translate non-empty text nodes
    for node in text_nodes:
        if node.strip():
            translated_text = translate_large_text(node.strip(), source_lang, target_lang, filename)
            node.replace_with(translated_text)

    # Convert the soup object back to a string
    translated_content = str(soup)

    return translated_content

def translate_html(html_string, filename, source_lang, target_lang):
    # Parse the HTML/XML using etree.parse()
    parser = etree.XMLParser(recover=True)
    tree = etree.parse(BytesIO(html_string.encode('utf-8')), parser)
    root = tree.getroot()
    
    # Check if there's any text content to translate
    text_content = root.xpath('//text()')
    if not any(text.strip() for text in text_content):
        print(f"No text content to translate in {filename}")
        return html_string
    
    # Translate text content
    for elem in root.iter():
        if elem.text and elem.text.strip():
            elem.text = translate_large_text(elem.text.strip(), source_lang, target_lang, filename)
        if elem.tail and elem.tail.strip():
            elem.tail = translate_large_text(elem.tail.strip(), source_lang, target_lang, filename)
    
    # Return the modified HTML as a string
    return etree.tostring(root, encoding='unicode', method='xml')

def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def write_file(file_path, content):
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def translate_opf(opf_path, output_path, source_lang, target_lang):
    """
    Translates the content of an OPF file, preserving the structure.
    """
    tree = etree.parse(opf_path)
    root = tree.getroot()
    ns = {'dc': 'http://purl.org/dc/elements/1.1/'}
    
    for elem in root.xpath('//dc:title | //dc:creator | //dc:description', namespaces=ns):
        if elem.text:
            elem.text = translate_large_text(elem.text, source_lang, target_lang, os.path.basename(opf_path))
    
    translated_content = etree.tostring(root, encoding='unicode', pretty_print=True)
    write_file(output_path, translated_content)
    print(f"Translated OPF file saved to {output_path}")

def translate_ncx(ncx_path, output_path, source_lang, target_lang):
    """
    Translates the content of an NCX file, preserving the structure.
    """
    tree = etree.parse(ncx_path)
    root = tree.getroot()
    
    for text_elem in root.xpath('//text'):
        if text_elem.text:
            text_elem.text = translate_large_text(text_elem.text, source_lang, target_lang, os.path.basename(ncx_path))
    
    translated_content = etree.tostring(root, encoding='unicode', pretty_print=True)
    write_file(output_path, translated_content)
    print(f"Translated NCX file saved to {output_path}")

# def estimate_token_count(epub_path):
#     """
#     Estimate token count based on paragraph text content within the EPUB file.
#     """
#     book = epub.read_epub(epub_path)
#     encoding = tiktoken.encoding_for_model("gpt-4o-mini")
#     total_tokens = 0

#     for item in book.get_items():
#         if item.get_type() == epub.ITEM_DOCUMENT:
#             soup = BeautifulSoup(item.get_content(), 'html.parser')
#             paragraphs = soup.find_all('p')
#             for p in paragraphs:
#                 text = p.get_text(strip=True)
#                 total_tokens += len(encoding.encode(text))

#     return total_tokens

def translate_all_files(xhtml_dir=None, ncx_path=None, opf_path=None, tags_to_remove=None, source_lang='English', target_lang='Spanish'):
    if tags_to_remove is None:
        tags_to_remove = ['span', 'sub', 'sup']

    total_tokens = 0

    # Translate XHTML/HTML files if xhtml_dir is provided
    if xhtml_dir:
        for filename in os.listdir(xhtml_dir):
            if filename.endswith('.xhtml') or filename.endswith('.html'):
                file_path = os.path.join(xhtml_dir, filename)
                content = read_file(file_path)
                content = preprocess(content, tags_to_remove)
                if filename.endswith('.xhtml'):
                    translated_content = translate_xhtml(content, filename, source_lang, target_lang)
                else:
                    translated_content = translate_html(content, filename, source_lang, target_lang)
                
                pattern = r'(<\?xml[^>]*>\s*)(?:html|HTML)(<html)'
                postprocessed_content = re.sub(pattern, r'\1\2', translated_content, flags=re.IGNORECASE, count=1)
                write_file(file_path, postprocessed_content)
                print(f"Processed and saved {filename}")

                # Estimate token count
                file_size = len(postprocessed_content.encode('utf-8'))
                # total_tokens += estimate_token_count(file_size)

    # Translate NCX file if ncx_path is provided
    if ncx_path:
        translate_ncx(ncx_path, ncx_path, source_lang, target_lang)
        file_size = len(read_file(ncx_path).encode('utf-8'))
        # total_tokens += estimate_token_count(file_size)

    # Translate OPF file if opf_path is provided
    if opf_path:
        translate_opf(opf_path, opf_path, source_lang, target_lang)
        file_size = len(read_file(opf_path).encode('utf-8'))
        # total_tokens += estimate_token_count(file_size)

    print(f"All specified files have been translated from {source_lang} to {target_lang} and saved.")

    return total_tokens

# Add this line at the end of the file to explicitly export the functions
__all__ = ['translate_all_files']
# 'estimate_token_count']
