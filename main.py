import fitz  # PyMuPDF for PDF processing
import os
import csv
import textstat
from textblob import TextBlob
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

# Define paths to the document folders
BASE_PATH = 'C:\\Users\\Shaurya\\Desktop\\Metrics Generation Project\\Dataset'
FOLDERS = ["Research Papers", "Whitepapers", "Scripts"]

def extract_text_from_pdf(pdf_path):
    """Extracts text from a single PDF file."""
    document = fitz.open(pdf_path)
    full_text = ''
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        full_text += page.get_text()
    document.close()
    return full_text

def grammatical_error_percentage(text):
    """
    Estimates the percentage of grammatical errors in the text based on corrections made by TextBlob.
    """
    original_blob = TextBlob(text)
    corrected_blob = original_blob.correct()
    
    original_words = word_tokenize(str(original_blob))
    corrected_words = word_tokenize(str(corrected_blob))
    
    # Count differences between original and corrected texts
    errors = sum(1 for original, corrected in zip(original_words, corrected_words) if original != corrected)
    
    total_words = len(original_words)
    error_percentage = (errors / total_words * 100) if total_words > 0 else 0
    
    return round(error_percentage, 2)

def calculate_readability(text):
    """Calculates readability score using textstat."""
    return textstat.flesch_reading_ease(text)

def average_sentence_length(text):
    """Computes average sentence length."""
    sentences = sent_tokenize(text)
    total_length = sum(len(sentence.split()) for sentence in sentences)
    return total_length / len(sentences) if sentences else 0

def find_repetitive_words(text):
    """Identifies repetitive words."""
    words = word_tokenize(text)
    freq_dist = nltk.FreqDist(words)
    repetitive_words = {word: count for word, count in freq_dist.items() if count > 1 and len(word) > 3}
    return repetitive_words

def assess_generic_content(text):
    """
    Estimates the percentage of the content that is generic based on the presence of filler words.
    """
    filler_words = [
        'basically', 'various', 'very', 'things', 'stuff', 
        'it is important', 'clearly', 'obviously', 'however', 
        'therefore', 'furthermore', 'in conclusion'
    ]
    words = word_tokenize(text)
    total_words = len(words)
    filler_word_count = sum(text.lower().count(word) for word in filler_words)
    generic_content_percentage = (filler_word_count / total_words * 100) if total_words > 0 else 0
    return round(generic_content_percentage, 2)


def detect_ai_content(text):
    """
    Estimates the percentage of the content that is likely AI-generated.
    """
    # Check for generic content
    generic_content_presence = assess_generic_content(text)
    generic_score = 0 if generic_content_presence else 1

    # Calculate repetitive word density
    words = word_tokenize(text)
    total_words = len(words)
    repetitive_words = find_repetitive_words(text)
    repetitive_word_count = sum(repetitive_words.values())
    repetitive_word_density = repetitive_word_count / total_words if total_words > 0 else 0

    # Consider average sentence length
    avg_sentence_len = average_sentence_length(text)
    sentence_length_score = 1 if avg_sentence_len < 15 else 0

    # Combine scores to estimate AI content percentage
    ai_content_score = (generic_score + repetitive_word_density + sentence_length_score) / 3
    ai_content_percentage = round(ai_content_score * 100, 2)

    return ai_content_percentage

def process_documents():
    """Processes documents and estimates various metrics, saving the results in a folder-specific CSV file."""
    print("Select the type of documents to analyze:")
    for idx, folder in enumerate(FOLDERS, start=1):
        print(f"{idx}. {folder}")
    choice = input("Enter your choice (number): ")

    try:
        chosen_folder = FOLDERS[int(choice) - 1]
    except (ValueError, IndexError):
        print("Invalid choice. Exiting...")
        return

    directory_path = os.path.join(BASE_PATH, chosen_folder)
    results = []

    for filename in os.listdir(directory_path):
        if filename.endswith('.pdf'):
            file_path = os.path.join(directory_path, filename)
            text = extract_text_from_pdf(file_path)

            error_percentage = grammatical_error_percentage(text)
            readability_score = calculate_readability(text)
            avg_sentence_len = average_sentence_length(text)
            repetitive_words = find_repetitive_words(text)
            ai_content_percentage = detect_ai_content(text)
            generic_content_percentage = assess_generic_content(text)

            results.append({
                'Filename': filename,
                'Grammatical Error Percentage': error_percentage,
                'Readability Score': readability_score,
                'Average Sentence Length': avg_sentence_len,
                'Repetitive Words': list(repetitive_words.keys()),
                'AI Content Percentage': ai_content_percentage,
                'Generic Content Percentage': generic_content_percentage,
            })

    # Output results to a CSV file named according to the chosen folder
    results_csv_path = f'{chosen_folder}_analysis_results.csv'
    with open(results_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Filename', 'Grammatical Error Percentage', 'Readability Score', 'Average Sentence Length', 'Repetitive Words', 'AI Content Percentage', 'Generic Content Percentage']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result)
    print(f"Analysis results saved in {results_csv_path}")



if __name__ == "__main__":
    process_documents()
