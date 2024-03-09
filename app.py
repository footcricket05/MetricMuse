import tkinter as tk
from tkinter import ttk, filedialog, Toplevel, messagebox
import os
import fitz  # PyMuPDF
from textblob import TextBlob
import textstat
from threading import Thread
import nltk
from nltk.tokenize import word_tokenize

# Ensure NLTK resources are available
nltk.download('punkt', quiet=True)

class MetricsApp:
    def __init__(self, root):
        self.root = root
        root.title("MetricMuse - Paper Metrics Analysis")
        root.geometry("600x400")

        self.upload_button = tk.Button(root, text="Upload Paper", command=self.upload_paper)
        self.upload_button.pack(pady=(100, 10))

        self.exit_button = tk.Button(root, text="Exit", command=root.destroy)
        self.exit_button.pack(pady=(10, 0))

    def extract_text_from_pdf(self, pdf_path):
        document = fitz.open(pdf_path)
        full_text = ''
        for page_num in range(len(document)):
            page = document.load_page(page_num)
            full_text += page.get_text()
        document.close()
        return full_text

    def generate_metrics(self, text):
        blob = TextBlob(text)
        original_words = text.split()
        corrected_words = str(blob.correct()).split()
        errors = sum(1 for original, corrected in zip(original_words, corrected_words) if original != corrected)
        error_percentage = (errors / len(original_words) * 100) if original_words else 0

        readability_score = textstat.flesch_reading_ease(text)

        sentences = textstat.sentence_count(text)
        avg_sentence_length = textstat.lexicon_count(text) / sentences if sentences else 0

        repetitive_words = self.find_repetitive_words(text)
        ai_content_percentage = self.detect_ai_content(text)
        generic_content_percentage = self.assess_generic_content(text)

        return {
            'Grammatical Error Percentage': round(error_percentage, 2),
            'Readability Score': readability_score,
            'Average Sentence Length': round(avg_sentence_length, 2),
            'Repetitive Words Count': len(repetitive_words),
            'AI Content Percentage': round(ai_content_percentage, 2),
            'Generic Content Percentage': round(generic_content_percentage, 2),
        }

    def find_repetitive_words(self, text):
        """Identifies repetitive words."""
        words = word_tokenize(text)
        freq_dist = nltk.FreqDist(words)
        repetitive_words = [word for word, count in freq_dist.items() if count > 1 and len(word) > 3]
        return repetitive_words

    def assess_generic_content(self, text):
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

    def detect_ai_content(self, text):
        """
        Estimates the percentage of the content that is likely AI-generated.
        """
        # Check for generic content
        generic_content_presence = self.assess_generic_content(text)
        generic_score = 0 if generic_content_presence else 1

        # Calculate repetitive word density
        words = word_tokenize(text)
        total_words = len(words)
        repetitive_words = self.find_repetitive_words(text)
        repetitive_word_count = len(repetitive_words)
        repetitive_word_density = repetitive_word_count / total_words if total_words > 0 else 0

        # Consider average sentence length
        sentences = textstat.sentence_count(text)
        avg_sentence_len = textstat.lexicon_count(text) / sentences if sentences else 0
        sentence_length_score = 1 if avg_sentence_len < 15 else 0

        # Combine scores to estimate AI content percentage
        ai_content_score = (generic_score + repetitive_word_density + sentence_length_score) / 3
        ai_content_percentage = round(ai_content_score * 100, 2)

        return ai_content_percentage

    def upload_paper(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file_path:
            # Create a thread to handle text extraction and metric generation
            process_thread = Thread(target=self.process_pdf, args=(file_path,))
            process_thread.start()

    def process_pdf(self, file_path):
        # Inform user that metrics are being generated
        generating_window = Toplevel(self.root)
        generating_window.title("MetricMuse - Generating Metrics")
        generating_window.geometry("300x100")
        generating_label = tk.Label(generating_window, text="Generating Metrics...")
        generating_label.pack(pady=30)

        text = self.extract_text_from_pdf(file_path)
        metrics = self.generate_metrics(text)

        # Close generating window
        generating_window.destroy()

        # Display the generated metrics
        self.show_results(metrics, "MetricMuse - Generated Metrics")

    def show_results(self, content, title):
        result_window = Toplevel(self.root)
        result_window.title(title)
        result_window.geometry("500x300")

        # Frame for metrics display
        frame = ttk.Frame(result_window)
        frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Header label
        header_label = ttk.Label(frame, text="Metrics", font=("Helvetica", 14, "bold"))
        header_label.grid(row=0, column=0, columnspan=2, pady=10)

        # Metric labels and values
        row = 1
        for metric, value in content.items():
            metric_label = ttk.Label(frame, text=metric + ":", font=("Helvetica", 12, "bold"))
            metric_label.grid(row=row, column=0, sticky="w", padx=5, pady=5)

            value_label = ttk.Label(frame, text=str(value), font=("Helvetica", 12))
            value_label.grid(row=row, column=1, sticky="w", padx=5, pady=5)

            row += 1

if __name__ == "__main__":
    root = tk.Tk()
    app = MetricsApp(root)
    root.mainloop()
