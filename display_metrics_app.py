import tkinter as tk
from tkinter import simpledialog, messagebox
import csv

class MetricsApp:
    def __init__(self, root):
        self.root = root
        root.title("Metrics Generation")
        root.geometry("400x300")

        self.label = tk.Label(root, text="Metrics Generation App", font=("Arial", 16))
        self.label.pack(pady=20)

        self.view_button = tk.Button(root, text="View Metrics", command=self.view_metrics)
        self.view_button.pack(pady=10)

        self.exit_button = tk.Button(root, text="Exit", command=root.destroy)
        self.exit_button.pack(pady=10)

    def calculate_average_metric(self, csv_file, metric_name):
        if metric_name == 'Repetitive Words Count':
            return self.calculate_average_repetitive_words(csv_file)
        
        total_metric_value = 0
        document_count = 0

        with open(csv_file, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if metric_name in row:
                    total_metric_value += float(row[metric_name])
                    document_count += 1

        if document_count > 0:
            average_metric = total_metric_value / document_count
            return average_metric
        else:
            print(f"No data found for metric '{metric_name}'.")
            return None

    def calculate_average_repetitive_words(self, csv_file):
        total_repetitive_words_count = 0
        document_count = 0

        with open(csv_file, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if 'Repetitive Words' in row:
                    repetitive_words = row['Repetitive Words'].split(", ")
                    total_repetitive_words_count += len(repetitive_words)
                    document_count += 1

        if document_count > 0:
            average_repetitive_words_count = total_repetitive_words_count / document_count
            return average_repetitive_words_count
        else:
            print(f"No data found for metric 'Repetitive Words Count'.")
            return None

    def view_metrics(self):
        # Prompt user for paper type
        paper_type = simpledialog.askinteger("Paper Type", "Enter paper type:\n1 for Research Papers\n2 for Whitepapers\n3 for Scripts")
        if paper_type in [1, 2, 3]:
            csv_file = f"C:\\Users\\Shaurya\\Desktop\\Metrics Generation Project\\{'Research Papers' if paper_type == 1 else 'Whitepapers' if paper_type == 2 else 'Scripts'}_analysis_results.csv"
            metrics = {}

            # Calculate metrics
            for metric_name in ['Grammatical Error Percentage', 'Readability Score', 'Average Sentence Length', 'AI Content Percentage', 'Generic Content Percentage', 'Repetitive Words Count']:
                average_metric = self.calculate_average_metric(csv_file, metric_name)
                if average_metric is not None:
                    metrics[metric_name] = f"{average_metric:.2f}"

            # Display metrics
            metric_display = "\n".join([f"{k}: {v}" for k, v in metrics.items()])
            messagebox.showinfo("Average Metrics", metric_display)
        else:
            messagebox.showerror("Error", "Invalid paper type. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    root = tk.Tk()
    app = MetricsApp(root)
    root.mainloop()
