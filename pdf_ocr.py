import pdfplumber
import pytesseract
import cv2
import numpy as np
import os


# Path to PDF file and tesseract path
pdf_path = './integrator/extractors/input_files/REALFLEX.pdf'
pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'
# Set TESSDATA_PREFIX environment variable to the path of the trained data directory
os.environ['TESSDATA_PREFIX'] = 'C:/Program Files/Tesseract-OCR/tessdata'


with pdfplumber.open(pdf_path) as pdf:
    for pagina in pdf.pages:
        # Extract image from page
        img = pagina.to_image().original
        img_arr = np.array(img)
        # Convert image to grayscale
        gray = cv2.cvtColor(img_arr, cv2.COLOR_BGR2GRAY)
        # Perform OCR using Pytesseract
        text = pytesseract.image_to_string(gray, lang="por")
        print(text)
