import os
import threading
import PyPDF2
import re
import datetime
import openai
from flask import Flask, render_template, request, jsonify
import tkinter as tk
import logging
import requests
from tqdm import tqdm
from tkinter import filedialog
from tkinter import simpledialog
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
from io import StringIO
from nltk.corpus import wordnet
import sys
import time
import nltk
import codecs
import random

api_key = "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"
openai.api_key = api_key

app = Flask(__name__)

class RedirectText:

  def __init__(self, widget):

    self.output = widget



  def write(self, string):

    self.output.insert(tk.END, string)

    self.output.see(tk.END)



  def flush(self):

    pass



logging.basicConfig(level=logging.INFO)



is_running = False

current_file = None

current_page = None 

summary_file = None



nltk.download('punkt')



from nltk.tokenize import sent_tokenize



logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

logger = logging.getLogger(__name__)  

logger.propagate = False  



def log_handler(record):

  process_text.configure(state='normal')

  process_text.insert(tk.END, f"{record.getMessage()}\n")

  process_text.configure(state='disabled')

  process_text.see(tk.END)



class InfoFilter(logging.Filter):

  def filter(self, record):

    return record.levelno == logging.INFO



class CustomStreamHandler(logging.StreamHandler):

  def emit(self, record):

    msg = self.format(record)

    process_text.configure(state='normal')

    process_text.insert(tk.END, f"{msg}\n")

    process_text.configure(state='disabled')

    process_text.see(tk.END)



hdlr = CustomStreamHandler()

hdlr.setLevel(logging.INFO)

hdlr.setFormatter(logging.Formatter(fmt="[%(levelname)s] %(message)s"))

hdlr.addFilter(InfoFilter())

logger.addHandler(hdlr)








def remove_apology_sentences(text):

  pattern = r"\\b(Xin lỗi|Vui lòng  đoạn|muốn dịch|văn cần dịch|có thể giúp bạn|Vui lòng  lại|Bạn có thể  đoạn|Xin lỗi anh|Xin vui lòng)[^.]*(\.|$)"

  filtered_text = re.sub(pattern, "", text, flags=re.IGNORECASE)

  return filtered_text



def detect_duplicated_summary(summary, summaries_list):

  if summary in summaries_list:

    return True

  return False



def custom_filter_1(text):

  question_phrases = [

    "bạn"

,    ]

  for phrase in question_phrases:

    text = re.sub(r'\\b' + phrase + r'\\b', "", text)

  return text



def custom_filter_2(text):

  apology_phrases = [

    "xin lỗi",

  ]

  for phrase in apology_phrases:

    text = re.sub(r'\\b' + phrase + r'\\b', "", text)

  return text



def custom_filter_3(text):

  info_phrases = [

    "cung cấp",

    "vui lòng gửi",

    "đưa ra",

  ]

  for phrase in info_phrases:

    text = re.sub(r'\\b' + phrase + r'\\b', "", text)

  return text



def custom_filter_4(text):

  language_phrases = [

    "Tiếng Trung",

    "Tiếng Anh", "Chinese",

  ]

  for phrase in language_phrases:

    text = re.sub(r'\\b' + phrase + r'\\b', "", text)

  return text



def apply_filters(text, filters):

  for filter_func in filters:

    text = filter_func(text)

  return text



def remove_unnecessary_words(text, synonym=True, filters=None):

  unnecessary_words = [

    'Please',

     ]

  words = text.split()

  filtered_words = [word for word in words if word not in unnecessary_words]

  filtered_text = ' '.join(filtered_words)

  

  filtered_text = apply_filters(filtered_text, filters) if filters else filtered_text

  return filtered_text



def remove_text_before_colon_if_needed(text):

  colon_index = text.find(":")

  if colon_index != -1:

    if "," not in text[:colon_index]:

      text = text[colon_index+1:].strip()

  return text



def custom_filter_6(text):

  colon_index = text.find(":")

  if colon_index != -1:

    text = text[colon_index+1:].strip()

    text = text.replace(":", "")

  return text



def remove_prefix(text, prefix):

  if text.startswith(prefix):

    text = text[len(prefix):].strip()

  return text



def summarize_pdf():

  global file_path



  logger = logging.getLogger(__name__)

  file_path = file_entry.get()

  output_filename = ""



  pdf_file = open(file_path, 'rb')

  pdf_reader = PyPDF2.PdfReader(pdf_file)

  pdf_summary_file = file_path.replace(os.path.splitext(file_path)[1], "_Bản Dịch.txt")

  total_token_used = 0

  i = 0

  i += 1



  summarized_text = []

  for page_num in range(len(pdf_reader.pages)):

    page_text = pdf_reader.pages[page_num].extract_text().lower()

    sentences = page_text.split(". ")

    

    chunks = split_paragraph(sentences)

    result_tex.delete(1.0, tk.END)

    for chunk in chunks:

      summary = None

      while not summary:

        summary = translate_and_summarize(chunk, page_num, len(pdf_reader.pages), summarized_text)

        if not summary:

          time.sleep(1)



      output_filename = os.path.splitext(file_path)[0] + "_Bản Dịch.txt"

      with open(output_filename, "a+", encoding="utf-8") as file:

        file.write(summary + "\\n\\n")



      num_tokens_sent = len(chunk.split())

      num_tokens_received = len(summary.split())

      TOKEN_EXCHANGE_RATE = 0.047

      total_token_used += num_tokens_received

      total_cost_vnd = total_token_used * TOKEN_EXCHANGE_RATE

      total_pages_list = len(chunks)



      result_text.insert(tk.END, f"{summary}\\n\\n")

      result_tex.insert(tk.END, f"Số token đã gửi đi cho lần {page_num + 1}: {num_tokens_sent}\\n")

      result_tex.insert(tk.END, f"Số token nhận về từ API cho lần {page_num + 1}: {num_tokens_received}\\n")

      result_tex.insert(tk.END, f"Tổng chi phí (VNĐ): {total_cost_vnd:.2f}\\n")

      result_tex.insert(tk.END, f"Số trang đã xử lý: {i}\\n")  

      result_tex.insert(tk.END, f"Số từ đã sử dụng: {total_token_used}\\n")

      result_text.see(tk.END)

      result_tex.see(tk.END)

      root.update()

    return jsonify({"summary": summary, "token_sent": num_tokens_sent, "token_received": num_tokens_received,
                    "total_cost_vnd": total_cost_vnd, "total_pages_processed": i, "total_tokens_used": total_token_used})


# New Flask route for rendering the HTML page
@app.route("/")
def index():
    return render_template("index.html")

# New Flask route for handling form submission
@app.route("/summarize", methods=["POST"])
def summarize():
    result = summarize_pdf()
    return render_template("result.html", result=result)




  

  pdf_file.close()



root = tk.Tk()

root.title("PDF Translator")



frame1 = tk.Frame(root)  

frame1.pack(pady=10)



file_label = tk.Label(frame1, text="File:")

file_label.pack(side=tk.LEFT)



file_entry = tk.Entry(frame1, width=50)

file_entry.pack(side=tk.LEFT) 



browse_button = tk.Button(frame1, text="Browse", command=browse_file)

browse_button.pack(side=tk.LEFT, padx=10)



summarize_button = tk.Button(frame1, text="Translate", command=summarize_pdf)

summarize_button.pack(side=tk.LEFT, padx=10)



root.mainloop()

if __name__ == "__main__":
    app.run(debug=True)
