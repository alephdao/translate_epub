import os
import zipfile
import re

def process_epub(epub_path, output_path, backup_path):
    # Ensure the output and backup directories exist
    os.makedirs(output_path, exist_ok=True)
    os.makedirs(backup_path, exist_ok=True)

    # Extract the EPUB contents
    extract_epub(epub_path, output_path, backup_path)

    # Find the directory containing .xhtml or .html files
    xhtml_path = find_xhtml_directory(output_path)
    ncx_path = find_file_by_pattern(output_path, r'.*toc\.ncx$')
    opf_path = find_file_by_pattern(output_path, r'.*content\.opf$')
    return xhtml_path, ncx_path, opf_path

def extract_epub(epub_path, output_path, backup_path):
    """
    Extracts the EPUB file to the specified output and backup paths.
    """
    # Create backup directory
    os.makedirs(backup_path, exist_ok=True)
    
    # Extract EPUB contents to backup path
    with zipfile.ZipFile(epub_path, 'r') as epub:
        epub.extractall(backup_path)
    
    # Copy extracted contents to output path
    for root, dirs, files in os.walk(backup_path):
        for file in files:
            src_path = os.path.join(root, file)
            rel_path = os.path.relpath(src_path, backup_path)
            dest_path = os.path.join(output_path, rel_path)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            os.rename(src_path, dest_path)

def find_xhtml_directory(output_path):
    """
    Finds the directory containing .xhtml or .html files within the output path.
    Prioritizes the '/text' folder if it exists, otherwise selects the folder
    with the most .xhtml or .html files.
    """
    text_folder = os.path.join(output_path, 'text')
    if os.path.isdir(text_folder) and any(f.endswith(('.xhtml', '.html')) for f in os.listdir(text_folder)):
        return text_folder

    xhtml_counts = {}
    for root, dirs, files in os.walk(output_path):
        xhtml_files = [f for f in files if f.endswith(('.xhtml', '.html'))]
        if xhtml_files:
            xhtml_counts[root] = len(xhtml_files)
    
    if xhtml_counts:
        return max(xhtml_counts, key=xhtml_counts.get)
    
    return None

def find_file_by_pattern(directory, pattern):
    """
    Finds a file matching the given regex pattern in the specified directory.
    """
    for root, dirs, files in os.walk(directory):
        for file in files:
            if re.match(pattern, file):
                return os.path.join(root, file)
    return None
