import streamlit as st
import os
import tempfile
from dotenv import load_dotenv
from epub_extract import process_epub
from epub_create import create_epub
from translate import main as translate
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

def main():
    st.title("EPUB Translator")

    # Check for API key in environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    
    # If API key is not in environment, prompt user to input it
    if not api_key:
        api_key = st.text_input("Enter your OpenAI API Key:", type="password")
        if not api_key:
            st.warning("Please enter a valid OpenAI API key to proceed.")
            return

    # Initialize OpenAI client only when API key is available
    client = None
    if api_key:
        try:
            client = OpenAI(api_key=api_key)
        except Exception as e:
            st.error(f"Failed to initialize OpenAI client: {e}")
            return

    # Check for model in environment variables
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Default to gpt-4o-mini

    # Prompt user for model if not set
    if not openai_model:
        openai_model = st.selectbox("Select OpenAI model:", ["gpt-3.5-turbo", "gpt-4o-mini", "gpt-4"])

    # File upload
    uploaded_file = st.file_uploader("Upload an EPUB file", type="epub")

    if uploaded_file is not None and client is not None:
        # Create a temporary directory to store the uploaded file
        with tempfile.TemporaryDirectory() as temp_dir:
            epub_path = os.path.join(temp_dir, uploaded_file.name)
            with open(epub_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Process the EPUB file
            output_path = os.path.join(temp_dir, "output")
            backup_path = os.path.join(temp_dir, "backup")
            xhtml_path, ncx_file_path, opf_file_path = process_epub(epub_path, output_path, backup_path)

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
                    
                    if all_files:
                        translate(xhtml_path, source_lang, target_lang, client, openai_model)
                        translated_paragraphs += total_paragraphs
                    else:
                        for file in files_to_translate:
                            translate(os.path.join(xhtml_path, file), source_lang, target_lang, client, openai_model)
                            translated_paragraphs += len(open(os.path.join(xhtml_path, file)).read().split('<p>')) - 1
                            
                            # Update progress bar
                            progress = (translated_paragraphs / total_paragraphs) * 100
                            st.progress(progress)

                st.success("Translation completed!")

                # Create the translated EPUB
                translated_epub_path = os.path.join(temp_dir, f"translated_{uploaded_file.name}")
                create_epub(output_path, translated_epub_path)

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
