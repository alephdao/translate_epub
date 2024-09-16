import re
import html

def preprocess(text, tags_to_remove):
    """
    Preprocess the text by removing specified tags, handling <i> and <b> tags, converting HTML entities to Unicode,
    and removing asterisks used in scene breaks.
    
    Args:
        text (str): Input text to process
        tags_to_remove (list): List of tag names to remove
    
    Returns:
        str: Processed text
    """
    # Convert HTML entities to Unicode
    text = html.unescape(text)

    # Remove specified tags while keeping their content
    for tag in tags_to_remove:
        # Pattern to match both self-closing and regular tags
        pattern = fr'<{tag}(?:\s+[^>]*)?(/>|>((?:(?!<{tag}).)*?)</{tag}>)'
        text = re.sub(pattern, r'\2', text, flags=re.DOTALL|re.IGNORECASE)

    # Process <i> and <b> tags
    def replace_formatting(match):
        tag = match.group(1)
        content = match.group(2)
        if re.match(r'^\w+$', content) and len(content) > 1:
            return f"<{tag}>{content}</{tag}>"
        else:
            return content

    pattern = r'<(i|b)>([^<]+)</\1>'
    text = re.sub(pattern, replace_formatting, text)

    # Remove asterisks used in scene breaks
    text = re.sub(r'\*+\s*\*+\s*\*+', '', text)

    return text

# Example usage for testing
# if __name__ == "__main__":
#     original = "<p>When I pushed open the door of the hospital room, Daddy&#x2019;s head slightly turned toward it, as if he knew I was about to arrive. <i>F</i>or a fleeting moment, his dim eyes livened up. I hugged Mother and Cheryl, then kissed his forehead&#x2014;it was moist and warm&#x2014;and sat by his side. * * *</p>"
#     processed = preprocess(original, ['sub'])
#     print(processed)
