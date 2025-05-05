import os
import re
import fitz
import docx

from embeddings import Embeddings

def parseDir(path):
    """
    Parse the directory and return a list of files that are ".pdf", ".docx", ".txt" or ".md" files.
    Args:
        path (str): The path to the directory to parse.
    Returns:   
        list: A list of files that are ".pdf", ".docx", ".txt" or ".md" files.
    """

    files = []
    for root, dirs, filenames in os.walk(path):
        # Ignore files in hidden directories and subdirectories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for filename in filenames:
            if filename.endswith(".pdf") or filename.endswith(".docx") or filename.endswith(".txt") or filename.endswith(".md"):
                files.append(os.path.join(root, filename))
    return files


def parseFile(file):
    """
    Parse the file and return the text content.
    Args:
        file (str): The path to the file to parse.
    Returns:
        str: The text content of the file.
    """
    if file.endswith(".pdf"):
        return parsePDF(file)
    elif file.endswith(".docx"):
        return parseDOCX(file)
    elif file.endswith(".txt"):
        return parseTXT(file)
    elif file.endswith(".md"):
        return parseMD(file)
    else:
        raise ValueError("Unsupported file type: {}".format(file))
    

def parsePDF(file):
    """
    Parse the PDF file and return the text content.
    Args:
        file (str): The path to the PDF file to parse.
    Returns:
        str: The text content of the PDF file.
    """
    doc = fitz.open(file)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

def parseDOCX(file):
    """
    Parse the DOCX file and return the text content.
    Args:
        file (str): The path to the DOCX file to parse.
    Returns:
        str: The text content of the DOCX file.
    """
    doc = docx.Document(file)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def parseTXT(file):
    """
    Parse the TXT file and return the text content.
    Args:
        file (str): The path to the TXT file to parse.
    Returns:
        str: The text content of the TXT file.
    """
    with open(file, "r", encoding="utf-8") as f:
        text = f.read()
    return text

def parseMD(file):
    """
    Parse the MD file and return the text content.
    Args:
        file (str): The path to the MD file to parse.
    Returns:
        str: The text content of the MD file.
    """
    with open(file, "r", encoding="utf-8") as f:
        text = f.read()
    # Remove markdown formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
    text = re.sub(r'`(.*?)`', r'\1', text)        # Inline code
    return text


def embedFiles(files, embedding: Embeddings):
    """
    Embed the files using the specified embedding model.
    Args:
        files (list): A list of files to embed.
        embedding (Embeddings): The embedding model to use.
    Returns:
        dict: A dictionary with filenames as keys and embeddings as values.
    """
    for file in files:
        text = parseFile(file)
        paragraphs = extractParagraphs(text)
        embeddings = embedding.get_embeddings(paragraphs)
        # Store the embeddings in a database or file
        embedding.save_embeddings(embeddings, file)
    return 



def extractParagraphs(text):
    """
    Extract paragraphs from the text content.
    Args:
        text (str): The text content to extract paragraphs from.
    Returns:
        list: A list of paragraphs.
    """
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    return paragraphs


if __name__ == "__main__":
    # Example usage in the current directory
    path = "./"
    files = parseDir(path)
    embedding = Embeddings(model_name="all-MiniLM-L6-v2", db_path="embeddings.db")
    embedFiles(files, embedding)

    print("Parsed files:")
    for file in files:
        print(file)

    # search for a query
    query = "LLM powered chatbots"
    results = embedding.search_embeddings(query, top_k=4)

    print("Top 4 results for query '{}':".format(query))
    for result in results:
        print(result)