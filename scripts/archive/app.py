import streamlit as st
import os
import tempfile
from epub_extract import process_epub
from translate import translate_all_files
# , estimate_token_count
from epub_create import create_epub

# def calculate_cost(token_count):
#     """
#     Calculate the estimated cost based on token count.
#     Current pricing: $0.002 per 1K tokens (for gpt-3.5-turbo)
#     """
#     return (token_count / 1000) * 0.002

def main():
    st.title("EPUB Translator (OpenAI)")

    # File upload
    uploaded_file = st.file_uploader("Choose an EPUB file", type="epub")

    # Language selection
    languages = ['English', 'Spanish', 'French', 'German', 'Italian', 'Portuguese', 'Russian', 'Japanese', 'Korean', 'Chinese']
    source_lang = st.selectbox("Select source language", languages, index=languages.index('English'))
    target_lang = st.selectbox("Select target language", languages, index=languages.index('Spanish'))

    if uploaded_file is not None:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.epub') as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_file_path = temp_file.name

        # Estimate token count and cost
        # estimated_tokens = estimate_token_count(temp_file_path)
        # estimated_cost = calculate_cost(estimated_tokens)
        
        # st.write(f"Estimated token count: {estimated_tokens:,}")
        # st.write(f"Estimated cost: ${estimated_cost:.2f}")

        # Clean up the temporary file
        os.unlink(temp_file_path)

        if st.button("Translate"):
            with st.spinner('Translating... This may take a while for large files.'):
                # Create temporary directories
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Save uploaded file
                    epub_path = os.path.join(temp_dir, "input.epub")
                    with open(epub_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    # Set up paths
                    output_path = os.path.join(temp_dir, "output")
                    backup_path = os.path.join(temp_dir, "backup")
                    os.makedirs(output_path, exist_ok=True)
                    os.makedirs(backup_path, exist_ok=True)

                    # Process EPUB
                    xhtml_path, ncx_file_path, opf_file_path = process_epub(epub_path, output_path, backup_path)

                    # Translate files
                    tags_to_remove = ['span', 'sub', 'sup']
                    actual_tokens = translate_all_files(
                        xhtml_dir=xhtml_path,
                        ncx_path=ncx_file_path,
                        opf_path=opf_file_path,
                        tags_to_remove=tags_to_remove,
                        source_lang=source_lang,
                        target_lang=target_lang
                    )
                    # actual_cost = calculate_cost(actual_tokens)

                    # st.write(f"Actual token count: {actual_tokens:,}")
                    # st.write(f"Actual cost: ${actual_cost:.2f}")

                    # Create translated EPUB
                    translated_epub_path = os.path.join(temp_dir, f"translated_{target_lang.lower()[:2]}.epub")
                    create_epub(output_path, translated_epub_path)

                    # Offer download
                    with open(translated_epub_path, "rb") as file:
                        st.download_button(
                            label="Download translated EPUB",
                            data=file,
                            file_name=f"translated_{target_lang.lower()[:2]}.epub",
                            mime="application/epub+zip"
                        )

            st.success("Translation completed!")

if __name__ == "__main__":
    main()
