# ctrl+shift+p -> Notebook: Select Notebook Kernel -> venv
from pdf2image import convert_from_path
from pytesseract import pytesseract
from PIL import Image, ImageFilter
import cv2
import os
import numpy as np
from matplotlib import pyplot as plt
import json
import threading


def convert_pdf_to_img(pdf_file):
    return convert_from_path(
        pdf_path=pdf_file, 
        dpi=500, 
        #output_folder="./output", 
        poppler_path=r"C:\Program Files\poppler-23.01.0\Library\bin",
        )


def convert_image_to_text(image):
    pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'
    return pytesseract.image_to_string(image, lang="por")


def save(img, name):
    cv2.imwrite(name, img)


def get_concat_v(im1, im2): # vertical image concatenation using PIL lib
    dst = Image.new('RGB', (im1.width, im1.height + im2.height))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (0, im1.height))
    return dst


def show(img_array):
    im = Image.fromarray(img_array)
    im.show()


def process_image(image, ksize, threshold = np.array([0])):
    if not np.any(threshold):
        # Apply grayscale to the image
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Apply blur
        blur = cv2.GaussianBlur(gray, (7, 7), 0)
        # Apply thresholding to the grayscale image
        _, threshold = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
    # Dilation 
    kernel = cv2.getStructuringElement(
        shape=cv2.MORPH_RECT, 
        ksize=ksize,
        ) # manual adjust of x, y dilation
    dilate = cv2.dilate(threshold, kernel, iterations=1)
    # Finding the Countours from the dilated image
    contours = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = contours[0] if len(contours)==2 else contours[1]
    contours = sorted(contours, key=lambda x: cv2.boundingRect(x)[1])
    return contours, image, threshold 

data_structures = {
    "Informações Gerais da Inscrição":[],
    "Informações Sobre os Valores da Inscrição":[],
    "Informações dos Devedores":[],
    "Natureza":[],
    "Informações sobre o parcelamento":[],
    "Informações sobre os pagamentos efetuados":[],
    "Informações de ocorrências":[],
}
data_structures_list = data_structures.keys()
current_data_struct = "Informações Gerais da Inscrição"
def get_text_consulta_inscricao(pdf_file):
    global data_structures, data_structures_list, current_data_struct
    threads_list=[]
    images = convert_pdf_to_img(pdf_file)
    w, h = images[0].size
    images = [image.crop((0, 100, w, h-100)) for image in images]
    im_v = get_concat_v(images[0].crop((0, 330, w, h-200)), images[1])
    for pg, image in enumerate(images[2:]):
        im_v = get_concat_v(im_v, image)
    # Process IMAGE and get The contours
    contours, image, threshold = process_image(np.array(im_v), ksize=(1400, 80))
    # Extracting each part
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if h > 200 and w > 800:
            cnts, cropped_image, _thrs = process_image(
                    image=image[y:y+h, x:x+w], 
                    threshold=threshold[y:y+h, x:x+w], 
                    ksize=(30, 17),
                )
            t = threading.Thread(target=start_threading_sentence, args=(cnts, _thrs))
            threads_list.append(t)
            t.start()
    
    # wait until all threads end up
    for t in threads_list:
        t.join()
    return data_structures

def start_threading_sentence(cnts, _thrs):
    global data_structures, data_structures_list, current_data_struct
    texts = []
    for _c in cnts:
        x, y, w, h = cv2.boundingRect(_c)
        if h < 150 and w > 10 and h > 50:
            thresholded_sentence = _thrs[y:y+h, x:x+w]
            text = convert_image_to_text(thresholded_sentence).strip().replace("\n", "")
            if len(text)!=0:
                if text in data_structures_list:
                    current_data_struct = text
                texts.append(text)
    data_structures[current_data_struct].append(texts)
    

if __name__ == "__main__":
    import time
    start_time = time.time()
    pdf_file = "REALFLEX.pdf"
    data_structures = get_text_consulta_inscricao(pdf_file)
    end_time = time.time()
    print(f"It took {end_time-start_time:.2f} seconds to compute")
    # SAVE
    
    with open("demo.json", "w", encoding="utf-8") as file:
        json.dump(data_structures, file)
