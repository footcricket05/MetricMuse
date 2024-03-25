import fitz  # PyMuPDF for PDF processing
import os
import re
import csv
import textstat
from textblob import TextBlob
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from concurrent.futures import ProcessPoolExecutor

# Ensure NLTK resources are available
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

# Define paths to the document folders
BASE_PATH = 'C:\\Users\\Shaurya\\Desktop\\Metrics Generation Project\\Dataset'
FOLDERS = ["Research Papers", "Whitepapers", "Scripts"]

def extract_text_from_pdf(pdf_path):
    document = fitz.open(pdf_path)
    full_text = ''
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        full_text += page.get_text()
    document.close()
    return full_text

def grammatical_error_percentage(text):
    original_blob = TextBlob(text)
    corrected_blob = original_blob.correct()
    original_words = word_tokenize(str(original_blob))
    corrected_words = word_tokenize(str(corrected_blob))
    errors = sum(1 for original, corrected in zip(original_words, corrected_words) if original != corrected)
    total_words = len(original_words)
    error_percentage = (errors / total_words * 100) if total_words > 0 else 0
    return round(error_percentage, 2)

def calculate_readability(text):
    return textstat.flesch_reading_ease(text)

def average_sentence_length(text):
    sentences = sent_tokenize(text)
    total_length = sum(len(sentence.split()) for sentence in sentences)
    return total_length / len(sentences) if sentences else 0

def find_repetitive_words(text):
    # Get the English stopwords
    stop_words = set(stopwords.words('english'))

    # Tokenize the text and filter out stopwords and short words
    words = [word.lower() for word in word_tokenize(text) if word.isalpha() and word.lower() not in stop_words and len(word) > 3]

    # Create a frequency distribution of the filtered words
    freq_dist = nltk.FreqDist(words)

    # Find repetitive words (appearing more than once)
    repetitive_words = {word: count for word, count in freq_dist.items() if count > 1}

    # Format the sorted words and counts for display
    repetitive_words_text = ', '.join([f"{word}: {count}" for word, count in repetitive_words.items()])

    return len(repetitive_words), repetitive_words_text

def assess_generic_content(text):
    filler_words = [
        'basically', 'various', 'very', 'things', 'stuff', 
        'it is important', 'clearly', 'obviously', 'however', 
        'therefore', 'furthermore', 'in conclusion'
    ]
    words = word_tokenize(text)
    total_words = len(words)
    filler_word_count = sum(len(re.findall(r'\b' + re.escape(word) + r'\b', text.lower())) for word in filler_words)
    generic_content_percentage = (filler_word_count / total_words * 100) if total_words > 0 else 0
    return round(generic_content_percentage, 2)

def detect_ai_content(text):
    generic_content_presence = assess_generic_content(text)
    generic_score = 0 if generic_content_presence else 1
    words = word_tokenize(text)
    total_words = len(words)
    repetitive_word_count, _ = find_repetitive_words(text)
    repetitive_word_density = repetitive_word_count / total_words if total_words > 0 else 0
    avg_sentence_len = average_sentence_length(text)
    sentence_length_score = 1 if avg_sentence_len < 15 else 0
    ai_content_score = (generic_score + repetitive_word_density + sentence_length_score) / 3
    ai_content_percentage = round(ai_content_score * 100, 2)
    return ai_content_percentage

def process_single_document(filename, directory_path):
    file_path = os.path.join(directory_path, filename)
    text = extract_text_from_pdf(file_path)
    error_percentage = grammatical_error_percentage(text)
    readability_score = calculate_readability(text)
    avg_sentence_len = average_sentence_length(text)
    repetitive_words_count, repetitive_words_text = find_repetitive_words(text)
    ai_content_percentage = detect_ai_content(text)
    generic_content_percentage = assess_generic_content(text)
    
    # Define the path for the full list of repetitive words file
    full_list_path = os.path.join(directory_path, f"{filename}_repetitive_words_full_list.txt")
    
    # Write the full list of repetitive words to the file with UTF-8 encoding
    with open(full_list_path, 'w', encoding='utf-8') as f:
        f.write(repetitive_words_text)
        
    limited_repetitive_words_text = ', '.join(repetitive_words_text.split(', ')[:10]) + '...'  # limit to first 10

    return {
        'Filename': filename,
        'Grammatical Error Percentage': error_percentage,
        'Readability Score': readability_score,
        'Average Sentence Length': avg_sentence_len,
        'Repetitive Words Count': repetitive_words_count,
        'Repetitive Words List (limited)': limited_repetitive_words_text,
        'Repetitive Words List (full)': full_list_path,
        'AI Content Percentage': ai_content_percentage,
        'Generic Content Percentage': generic_content_percentage,
    }

    if not text.strip():
        print(f"No extractable text found in {filename}.")

def process_documents():
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

    # Set up a process pool to handle parallel document processing
    with ProcessPoolExecutor() as executor:
        # Submit tasks to the process pool for each PDF file
        futures = [executor.submit(process_single_document, filename, directory_path) 
                   for filename in os.listdir(directory_path) if filename.endswith('.pdf')]

        # Collect results as they are completed
        for future in futures:
            try:
                result = future.result()
                results.append(result)
            except Exception as exc:
                print(f'An exception occurred while processing a document: {exc}')

    # Output results to a CSV file in the base directory (not inside the Dataset directory)
    results_csv_path = os.path.join('C:\\Users\\Shaurya\\Desktop\\Metrics Generation Project', f'{chosen_folder}_analysis_results.csv')
    with open(results_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Filename', 'Grammatical Error Percentage', 'Readability Score', 'Average Sentence Length',
                      'Repetitive Words Count', 'Repetitive Words List (limited)', 'Repetitive Words List (full)',
                      'AI Content Percentage', 'Generic Content Percentage']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result)
    
    print(f"Analysis results saved in {results_csv_path}")

    if not results:
        print("No results generated. Please check the input documents and paths.")


if __name__ == "__main__":
    process_documents()

