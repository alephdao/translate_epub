import os
import zipfile
import shutil

def create_epub(input_folder, output_epub):
    """
    Create an EPUB file from the contents of the input folder.
    
    Args:
        input_folder (str): Path to the folder containing EPUB contents.
        output_epub (str): Path to the output EPUB file.
    """
    # Create a temporary directory for building the EPUB
    temp_dir = 'temp_epub'
    os.makedirs(temp_dir, exist_ok=True)

    # Copy all files from input_folder to temp_dir
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            src_path = os.path.join(root, file)
            dst_path = os.path.join(temp_dir, os.path.relpath(src_path, input_folder))
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            shutil.copy2(src_path, dst_path)

    # Ensure the mimetype file exists and is the first file in the EPUB
    mimetype_path = os.path.join(temp_dir, 'mimetype')
    if not os.path.isfile(mimetype_path):
        raise FileNotFoundError("The 'mimetype' file is missing in the input folder.")

    # Create the EPUB file
    with zipfile.ZipFile(output_epub, 'w', zipfile.ZIP_DEFLATED) as epub:
        # Add mimetype file first (it should not be compressed)
        epub.write(mimetype_path, 'mimetype', compress_type=zipfile.ZIP_STORED)

        # Add all other files
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file != 'mimetype':
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    epub.write(file_path, arcname)

    # Clean up temporary directory
    shutil.rmtree(temp_dir)

    print(f"EPUB file created: {output_epub}")

# Usage
# input_folder = '../output/hillbilly-elegy/epub'
# output_epub = './hillbilly-elegy_spanish.epub'

# create_epub(input_folder, output_epub)
