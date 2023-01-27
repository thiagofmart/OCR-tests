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
        dpi=430, 
        #output_folder="./output", 
        poppler_path=r"C:\Program Files\poppler-23.01.0\Library\bin",
        )


def convert_image_to_text(image):
    pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'
    return pytesseract.image_to_string(image, lang="perf")


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
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
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
    "Informações Sobre os Débitos da Inscrição":[],
    "Informações sobre o parcelamento":[],
    "Informações sobre os pagamentos efetuados":[],
    "Informações de ocorrências":[],
    "Outros": []
}
data_structures_list = data_structures.keys()
def get_text_consulta_inscricao(pdf_file, super_counter):
    global data_structures, data_structures_list
    threads_list=[]
    images = convert_pdf_to_img(pdf_file)
    w, h = images[0].size
    images = [image.crop((0, 100, w, h-100)) for image in images]
    if len(images)>1:
        im_v = get_concat_v(images[0].crop((0, 330, w, h-200)), images[1])
        for image in images[2:]:
            im_v = get_concat_v(im_v, image)
    else:
        im_v = images[0].crop((0, 330, w, h-200))
    # Process IMAGE and get The contours
    contours, image, threshold = process_image(np.array(im_v), ksize=(1400, 80))
    del im_v
    # Extracting each part
    counter = 0
    for c in contours[:-1]:
        x, y, w, h = cv2.boundingRect(c)
        if h > 200 and w > 800:
            cnts, cropped_image, _thrs = process_image(
                    image=image[y:y+h, x:x+w], 
                    threshold=threshold[y:y+h, x:x+w], 
                    ksize=(30, 17),
                )
            t = threading.Thread(target=start_threading_sentence, args=(cnts, _thrs, counter, super_counter))
            counter+=1
            threads_list.append(t)
            t.start()
    
    # wait until all threads end up
    for t in threads_list:
        t.join()
    return data_structures

def insert_data_pair(data_pair, dct):
    data_pair_copy = data_pair
    if ("\nValor Remanescente" in data_pair_copy) or ("\nValor Origináro" in data_pair_copy):
        print(data_pair_copy+"\n"+"-"*20)
    data_pair = data_pair.split(":")
    if len(data_pair)==1:
        pass
    elif len(data_pair)==2:
        dct[data_pair[0]] = data_pair[1].strip()
    else:
        data_pairs = data_pair_copy.split("\n")
        for data_pair in data_pairs:
            dct = insert_data_pair(data_pair, dct)
    return dct


def start_threading_sentence(cnts, _thrs, counter, super_counter):
    global data_structures, data_structures_list
    texts = {}
    ind = None
    count=0
    validate_chars = ["ç", "ã", "õ", "ó", "í", "é", "$", "Multa", "UFIR", "Valor"]
    for _c in cnts:
        x, y, w, h = cv2.boundingRect(_c)
        if h < 150 and w > 10 and h > 50:
            thresholded_sentence = _thrs[y:y+h, x:x+w]
            text = convert_image_to_text(thresholded_sentence)
            # if any(char in text for char in validate_chars) or text.endswith(" O"):
            save(thresholded_sentence, f"./output_image/sentence_{super_counter}-{counter}-{count}.jpg")
            # with open(f"./output_text/sentence_{super_counter}-{counter}-{count}.txt", "w", encoding="utf-8") as file:
            #     file.write(text)
            count+=1
            text = text.strip()
            try:
                texts = insert_data_pair(text, texts)
            except RecursionError:
                print(f"Erro na string '{text}'")
            if not ind:
                if "Informações Gerais da Inscrição" in text: 
                    ind = "Informações Gerais da Inscrição"
                elif ("Informações Sobre os Valores da Inscrição" in text) or (("Principal" in text) and not ("Devedor" in text)): 
                    ind = "Informações Sobre os Valores da Inscrição"
                elif ("Informações dos Devedores" in text) or ("Situação Cadastral" in text):
                    ind = "Informações dos Devedores"
                elif "Natureza" in text:
                    ind = "Informações Sobre os Débitos da Inscrição"
                elif "Informações sobre o parcelamento" in text:
                    ind = "Informações sobre o parcelamento"
                elif "Informações sobre os pagamentos efetuados" in text:
                    ind = "Informações sobre os pagamentos efetuados" 
                elif "Informações de ocorrências" in text:
                    ind = "Informações de ocorrências"
    data_structures[ind].append(texts) if ind else data_structures["Outros"].append(texts)

if __name__ == "__main__":
    import time
    input_dir = "./input_pdf"
    pdf_files = [f for f in os.listdir(input_dir) if f.endswith((".pdf",))]
    pdf_file = "REALFLEX.pdf"
    super_counter = 1
    for pdf_file in pdf_files[76:77]:
        start_time = time.time()
        data_structures = get_text_consulta_inscricao(f"./input_pdf/{pdf_file}", super_counter)
        super_counter+=1
        end_time = time.time()
        print(f"It took {end_time-start_time:.2f} seconds to compute")
        print(pdf_file)
        with open("demo.json", "w", encoding="utf-8") as file:
            json.dump(data_structures, file)
    # SAVE

