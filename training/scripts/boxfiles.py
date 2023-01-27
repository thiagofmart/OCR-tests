# reads all the image files present in data dir and creates corresponding box files.
# Files need to have the correct naming convention.
import os
os.chdir('./output_image')
number_of_files = len(os.listdir('./'))
os.environ['TESSDATA_PREFIX'] = 'C:/Program Files/Tesseract-OCR/tessdata'
for i in range(51, number_of_files):
    os.system(f"tesseract perf.ocrb.exp{i}.jpg perf.ocrb.exp{i} -l perf+por batch.nochop makebox")
