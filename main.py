from pdf2image import convert_from_path
from pytesseract import pytesseract
from PIL import Image



def convert_pdf_to_img(pdf_file):
    return convert_from_path(
        pdf_path=pdf_file, 
        dpi=500, 
        #output_folder="./output", 
        poppler_path=r"C:\Program Files\poppler-0.68.0\bin"
        )


def convert_image_to_text(file):
    pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    return pytesseract.image_to_string(file, lang="por")


def get_text_from_any_pdf(pdf_file):
    images = convert_pdf_to_img(pdf_file)
    final_text = ""
    #
    for pg, img in enumerate(images):
        final_text += convert_image_to_text(img)
    return final_text


def get_concat_v(im1, im2):
    dst = Image.new('RGB', (im1.width, im1.height + im2.height))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (0, im1.height))
    return dst
if __name__ == "__main__":
    pdf_file = "REALFLEX.pdf"
    images = convert_pdf_to_img(pdf_file)
    for pg, image in enumerate(images):
        image.save(f"./output/pagina_{pg}.png")
    
    im_v = get_concat_v(images[0], images[1])
    for pg, image in enumerate(images[2:]):
        im_v = get_concat_v(im_v, image)
