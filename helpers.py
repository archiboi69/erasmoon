import re
import unidecode

def sanitize_filename(filename):
    # Remove accents
    filename = unidecode.unidecode(filename)
    # Convert to lowercase
    filename = filename.lower()
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    # Remove any non-word characters (everything except numbers and letters)
    filename = re.sub(r'[^\w\s-]', '', filename)
    # Clean up multiple dashes or whitespaces
    filename = re.sub(r'[-\s]+', '-', filename).strip('-_')
    return filename
