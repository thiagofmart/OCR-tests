from pdf2image import convert_from_path
from pytesseract import pytesseract
from PIL import Image, ImageFilter
import cv2
import os


def convert_pdf_to_img(pdf_file):
    return convert_from_path(
        pdf_path=pdf_file, 
        dpi=500, 
        #output_folder="./output", 
        poppler_path=r"C:\Program Files\poppler-23.01.0\Library\bin",
        )


def convert_image_to_text(file):
    pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'
    return pytesseract.image_to_string(file)


def get_text_from_any_pdf(pdf_file):
    images = convert_pdf_to_img(pdf_file)
    final_text = ""
    #
    for pg, img in enumerate(images):
        final_text += convert_image_to_text(img)
    return final_text

def save(img, name):
    cv2.imwrite(name, img)

def get_concat_v(im1, im2):
    dst = Image.new('RGB', (im1.width, im1.height + im2.height))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (0, im1.height))
    return dst
if __name__ == "__main__":
    pdf_file = "REALFLEX.pdf"
    # take the images of each page from pdf file
    images = convert_pdf_to_img(pdf_file)
    # concatenate all the pages vertically into one image    
    im_v = get_concat_v(images[0], images[1])
    for pg, image in enumerate(images[2:]):
        im_v = get_concat_v(im_v, image)
    # Convert the PIL image to a cv2 image
    cv2_img = cv2.cvtColor(np.array(im_v), cv2.COLOR_RGB2BGR)
    # Apply grayscale to the image
    gray = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2GRAY)
    # Apply thresholding to the grayscale image
    _, threshold = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY)
    # Apply Dilation
    kernal = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 30))
    dilate = cv2.dilate(threshold, kernal, iterations=1)
    # Apply the blur filter to the threshold image
    #blur = cv2.GaussianBlur(threshold, (1, 1), 1)
    # Find the contours of the blur image
    contours = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = contours[0] if len(contours) == 2 else contours[1]
    cnts = sorted(cnts, key=lambda x: cv2.boundingRect(x)[1])
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        cv2.rectangle(threshold, (x, y), (x+w, y+h), (36, 266, 12), 2)
    # Draw the contours on the threshold image
    cv2_img = cv2.drawContours(threshold, contours, -1, (0, 255, 0), 2)



