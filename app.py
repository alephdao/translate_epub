import streamlit as st
import os
import tempfile
from dotenv import load_dotenv
from epub_extract import process_epub
from epub_create import create_epub
from translate import translate_text
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Set page config at the very beginning
st.set_page_config(page_title="EPUB Translator", layout="wide")

# Function to get API key from environment or user input
def get_api_key(key_name, env_var_name):
    api_key = os.getenv(env_var_name)
    if not api_key:
        # Prompt user to input API key if not found in environment
        api_key = st.text_input(f"Enter your {key_name} API key:", type="password")
    return api_key

def main():
    st.title("EPUB Translator")

    # Set up API keys
    OPENAI_API_KEY = get_api_key("OpenAI", 'OPENAI_API_KEY')
    OPENAI_MODEL = st.text_input("Enter your OpenAI model (e.g., gpt-3.5-turbo):", value="gpt-3.5-turbo")

    # Initialize client
    client = None
    if OPENAI_API_KEY:
        try:
            client = OpenAI(api_key=OPENAI_API_KEY)
        except Exception as e:
            st.error(f"Failed to initialize OpenAI client: {str(e)}")
            return
    else:
        st.warning("Please enter your OpenAI API key to use the application.")
        return

    # File upload
    uploaded_file = st.file_uploader("Upload an EPUB file", type="epub")

    if uploaded_file is not None:
        # Create a temporary directory to store the uploaded file
        with tempfile.TemporaryDirectory() as temp_dir:
            epub_path = os.path.join(temp_dir, uploaded_file.name)
            with open(epub_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Process the EPUB file
            output_path = os.path.join(temp_dir, "output")
            backup_path = os.path.join(temp_dir, "backup")
            try:
                xhtml_path, ncx_file_path, opf_file_path = process_epub(epub_path, output_path, backup_path)
            except Exception as e:
                st.error(f"Error processing EPUB file: {str(e)}")
                return

            # Language selection
            source_lang = st.selectbox("Select source language", ["English", "Spanish", "French", "German"])
            target_lang = st.selectbox("Select target language", ["Spanish", "English", "French", "German"])

            # File selection
            st.write("Select files to translate:")
            all_files = st.checkbox("Translate all files", value=True)
            
            if not all_files:
                files_to_translate = st.multiselect("Select specific files to translate", os.listdir(xhtml_path))

            # Translate button
            if st.button("Translate"):
                with st.spinner("Translating..."):
                    # Count total paragraphs in HTML files for progress tracking
                    total_paragraphs = sum(len(open(os.path.join(xhtml_path, file)).read().split('<p>')) - 1 for file in os.listdir(xhtml_path))
                    translated_paragraphs = 0
                    
                    progress_bar = st.progress(0)
                    
                    try:
                        if all_files:
                            for file in os.listdir(xhtml_path):
                                translate_text(os.path.join(xhtml_path, file), source_lang, target_lang, client, OPENAI_MODEL)
                                translated_paragraphs += len(open(os.path.join(xhtml_path, file)).read().split('<p>')) - 1
                                progress = (translated_paragraphs / total_paragraphs)
                                progress_bar.progress(progress)
                        else:
                            for file in files_to_translate:
                                translate_text(os.path.join(xhtml_path, file), source_lang, target_lang, client, OPENAI_MODEL)
                                translated_paragraphs += len(open(os.path.join(xhtml_path, file)).read().split('<p>')) - 1
                                progress = (translated_paragraphs / total_paragraphs)
                                progress_bar.progress(progress)
                    except Exception as e:
                        st.error(f"Error during translation: {str(e)}")
                        return

                st.success("Translation completed!")

                # Create the translated EPUB
                translated_epub_path = os.path.join(temp_dir, f"translated_{uploaded_file.name}")
                try:
                    create_epub(output_path, translated_epub_path)
                except Exception as e:
                    st.error(f"Error creating translated EPUB: {str(e)}")
                    return

                # Offer download of the translated EPUB
                with open(translated_epub_path, "rb") as file:
                    st.download_button(
                        label="Download translated EPUB",
                        data=file,
                        file_name=f"translated_{uploaded_file.name}",
                        mime="application/epub+zip"
                    )

if __name__ == "__main__":
    main()
