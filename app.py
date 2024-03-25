import tkinter as tk
from tkinter import ttk, filedialog, Toplevel, messagebox
import os
import csv
import fitz  # PyMuPDF
from textblob import TextBlob
import textstat
from tkinter import simpledialog, messagebox
from threading import Thread
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

# Ensure NLTK resources are available
nltk.download('punkt', quiet=True)
nltk.download('stopwords')

class MetricsApp:
    def __init__(self, root):
        self.root = root
        root.title("MetricMuse - Paper Metrics Analysis")
        root.geometry("600x400")

        # Container frame for buttons to assist in centering
        self.button_frame = tk.Frame(root)
        self.button_frame.pack(pady=100)  # Adjust vertical padding as needed

        self.view_button = tk.Button(self.button_frame, text="View Metrics", command=self.view_metrics)
        self.view_button.pack(side=tk.LEFT, padx=20)  # Adjust horizontal padding as needed

        self.upload_button = tk.Button(self.button_frame, text="Upload Paper", command=self.upload_paper)
        self.upload_button.pack(side=tk.LEFT, padx=20)  # Adjust horizontal padding as needed

        # Separate frame for the Exit button to provide additional space from other buttons
        self.exit_frame = tk.Frame(root)
        self.exit_frame.pack(pady=25)  # Adjust vertical padding as needed
        self.exit_button = tk.Button(self.exit_frame, text="Exit", command=root.destroy)
        self.exit_button.pack()  # No side needed as it's the only widget in this frame


    def calculate_average_metric(self, csv_file, metric_name):
        total_metric_value = 0
        document_count = 0

        with open(csv_file, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if metric_name in row and row[metric_name]:
                    try:
                        total_metric_value += float(row[metric_name])
                        document_count += 1
                    except ValueError:
                        pass  # Ignore rows where the metric is not a valid float

        if document_count > 0:
            average_metric = total_metric_value / document_count
            return average_metric
        else:
            print(f"No data found for metric '{metric_name}'.")
            return None

    def view_metrics(self):
        paper_type = simpledialog.askinteger("Paper Type", "Enter paper type:\n1 for Research Papers\n2 for Whitepapers\n3 for Scripts")
        if paper_type in [1, 2, 3]:
            paper_type_str = ['Research Papers', 'Whitepapers', 'Scripts'][paper_type - 1]
            csv_file = f"C:\\Users\\Shaurya\\Desktop\\Metrics Generation Project\\{'Research Papers' if paper_type == 1 else 'Whitepapers' if paper_type == 2 else 'Scripts'}_analysis_results.csv"
            metrics = {}

            for metric_name in ['Grammatical Error Percentage', 'Readability Score', 'Average Sentence Length', 'Repetitive Words Count', 'AI Content Percentage', 'Generic Content Percentage']:
                average_metric = self.calculate_average_metric(csv_file, metric_name)
                if average_metric is not None:
                    metrics[metric_name] = f"{average_metric:.2f}"

            metric_display = "\n".join([f"{k}: {v}" for k, v in metrics.items()])
            messagebox.showinfo("Average Metrics for " + paper_type_str, metric_display)
        else:
            messagebox.showerror("Error", "Invalid paper type. Please enter 1, 2, or 3.")

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

        repetitive_words_count, repetitive_words_text = self.find_repetitive_words(text)
        ai_content_percentage = self.detect_ai_content(text)
        generic_content_percentage = self.assess_generic_content(text)

        return {
            'Grammatical Error Percentage': round(error_percentage, 2),
            'Readability Score': readability_score,
            'Average Sentence Length': round(avg_sentence_length, 2),
            'Repetitive Words Count': repetitive_words_count,
            'Repetitive Words List': repetitive_words_text,
            'AI Content Percentage': round(ai_content_percentage, 2),
            'Generic Content Percentage': round(generic_content_percentage, 2),
        }

    def find_repetitive_words(self, text):
        # Define the set of stopwords
        stop_words = set(stopwords.words('english'))

        # Tokenize the text and filter out stopwords and short words
        words = [word.lower() for word in word_tokenize(text) if word.isalpha() and word.lower() not in stop_words]

        # Create a frequency distribution of the filtered words
        freq_dist = nltk.FreqDist(words)

        # Identify words that appear more than once and are longer than 3 characters
        repetitive_words = {word: count for word, count in freq_dist.items() if count > 1 and len(word) > 3}

        # Sort the words by their frequency
        sorted_repetitive_words = sorted(repetitive_words.items(), key=lambda kv: kv[1], reverse=True)

        # Format the sorted words and counts for display
        repetitive_words_text = ', '.join([f"{word}: {count}" for word, count in sorted_repetitive_words])

        return len(repetitive_words), repetitive_words_text

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
        repetitive_word_count, _ = self.find_repetitive_words(text)  # Use '_' if the list is not needed
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
        generating_window.geometry("500x300")
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
        result_window.geometry("800x600")

        # Frame for metrics display
        frame = ttk.Frame(result_window)
        frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Header label
        header_label = ttk.Label(frame, text="Metrics", font=("Helvetica", 14, "bold"))
        header_label.grid(row=0, column=0, columnspan=2, pady=10)

        # Metric labels and values, except for the repetitive words list
        row = 1
        for metric, value in content.items():
            if metric != 'Repetitive Words List':
                metric_label = ttk.Label(frame, text=metric + ":", font=("Helvetica", 12, "bold"))
                metric_label.grid(row=row, column=0, sticky="w", padx=5, pady=5)

                value_label = ttk.Label(frame, text=str(value), font=("Helvetica", 12))
                value_label.grid(row=row, column=1, sticky="w", padx=5, pady=5)

                row += 1

        # Special handling for Repetitive Words List to use a Text widget with scrollbar for better display
        repetitive_words_label = ttk.Label(frame, text="Repetitive Words List:", font=("Helvetica", 12, "bold"))
        repetitive_words_label.grid(row=row, column=0, sticky="nw", padx=5, pady=5)

        # Create a Text widget and a Scrollbar and pack them
        repetitive_words_text = tk.Text(frame, wrap="word", height=6, width=40)  # Adjust height and width as needed
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=repetitive_words_text.yview)
        repetitive_words_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=row, column=2, sticky='ns', padx=5, pady=5)
        repetitive_words_text.grid(row=row, column=1, sticky="w", padx=5, pady=5)
        repetitive_words_text.insert("1.0", content['Repetitive Words List'])
        repetitive_words_text.config(state="disabled")  # To make the text read-only


if __name__ == "__main__":
    root = tk.Tk()
    app = MetricsApp(root)
    root.mainloop()
