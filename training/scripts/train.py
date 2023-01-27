# Run after annotating all the box files generated from boxfiles.py
# https://github.com/nguyenq/jTessBoxEditor/releases/tag/Release-2.3.1 can be used for annotating.

import os
import subprocess

ROOT = "training/"
srcdir = ROOT+'data' # <- input the .box and .jpg files here
destdir = ROOT+'trainfiles'
os.environ['TESSDATA_PREFIX'] = 'C:/Program Files/Tesseract-OCR/tessdata'

# Removing all previous trained files.
try:
    os.remove(ROOT+'tessdata/perf.traineddata')
except OSError:
    pass

#### Collecting All the box files and images and create a tuple.
files = os.listdir(srcdir)
for item in files:
    if not item.endswith(('.jpg', '.box')):
        os.remove(os.path.join(srcdir, item))
# Generating the tuples of filenames
files = os.listdir(srcdir)
jpgs = [x for x in files if x.endswith('.jpg')]
boxes = [x for x in files if x.endswith('.box')]
trainfiles = list(zip(jpgs, boxes))


# For every image/boxfile in the list, first check if train data was 
# generated for the image, if not we run:
#     tesseract {srcdir}/{image} {destdir}/{image[:-4]} nobatch box.train
# generating TR files and unicode charecter extraction
unicharset = f"unicharset_extractor --output_unicharset ../../{destdir}/unicharset "
unicharset_args = f""
errorfiles = []
for image, box in trainfiles:
    unicharset_args += f"{box} "
    if os.path.isfile(f"{destdir}/{image[:-4]}.tr"):
        continue
    try:
        print(image)
        os.system(f"tesseract {srcdir}/{image} {destdir}/{image[:-4]} nobatch box.train")
    except:
        errorfiles.append((image, box))
os.chdir(srcdir)
subprocess.run(unicharset+unicharset_args)
os.chdir('../../')

# Once we generate train files. We write a file called font_properties
# Each line of the font_properties file is formatted as follows:
# "{fontname:str} {italic:int|bool} {bold:int|bool} {fixed:int|bool} {serif:int|bool} {fraktur:int|bool}"
# like: "ocrb 0 0 0 1 0"
with open(f"{destdir}/font_properties", 'w') as f:
    f.write("ocrb 0 0 0 1 0")

# # Getting all .tr files and training
# Append all the files to the mftraining and entrainning commands and run them.
# This will give us a charset file for our language and 4 other fukes on the trianoutput directory
output = '../../training/trainoutput'
trfiles = [f for f in os.listdir(destdir) if f.endswith('.tr')]
os.chdir(destdir)
mftraining = f"mftraining -F font_properties -U unicharset -O {output}/perf.unicharset -D {output}"
cntraining = f"cntraining -D {output}"
for file in trfiles:
    mftraining += f" {file}"
    cntraining += f" {file}"
subprocess.run(mftraining)
subprocess.run(cntraining)
os.chdir('../../')

# # Renaming training files and merging them
os.chdir(output[6:])
os.rename('inttemp', 'perf.inttemp')
os.rename('normproto', 'perf.normproto')
os.rename('pffmtable', 'perf.pffmtable')
os.rename('shapetable', 'perf.shapetable')
os.system(f"combine_tessdata perf.")

# Writing log file
if len(errorfiles) == 0:
    errorfiles.append(('no', 'Error'))
with open(ROOT+'scripts/logs.txt', 'w') as f:
    f.write('\n'.join('%s %s' % x for x in errorfiles))