Usage
- put a epub in the input folder
- run the extract
- specify the folder where the html files to translate are
- create the new ebook. 

it will go html tag by tag. so it's a bit slow. could process input files simultaneously though. probably 1-2 minutes per epub. 

# Improvements

- make this an app 
- update main.py to use the new translate_simple
- test it on more books ... ideally public domain ones. 


# Notes


The translation code is in a good place. What you can do is either run the translate simple on one part or you can run it on the entire code and you basically are switching out the contents of the HTML files and you create a new EPUB with those HTML files. It works really well.

The basic approach is just to only process the actual text part of the HTML and to skip all their tags and to also remove any of the inline tags from that text part like a paragraph tag so that the llms don't have any problems
