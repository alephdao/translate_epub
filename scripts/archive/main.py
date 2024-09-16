import os
from epub_extract import process_epub
from epub_create import create_epub
from translate import main as translate


def main():
    book_name = 'common_sense'
    epub_path = os.path.abspath(f'../input/{book_name}.epub')
    output_path = os.path.abspath(f'../output/{book_name}/epub')
    backup_path = os.path.abspath(f'../output/{book_name}/backup')

    # Specify source and target languages
    source_lang = 'English'
    target_lang = 'Spanish'

    # xhtml_path, ncx_file_path, opf_file_path = process_epub(epub_path, output_path, backup_path)
    # print(f"XHTML/HTML folder: {xhtml_path}")
    # print(f"NCX file: {ncx_file_path}")
    # print(f"OPF file: {opf_file_path}")
    # print(f"Backup path: {backup_path}")

    # translate(xhtml_path)
    
    create_epub(output_path, f'../output/{book_name}/{book_name}_{target_lang.lower()[:2]}.epub')

    # print(f"All files have been translated from {source_lang} to {target_lang} and saved to their original locations.")


if __name__ == "__main__":
    main()
