import argparse
from PIL import Image, ImageOps, ImageChops

parser = argparse.ArgumentParser(description="Textify Images With Python")

parser.add_argument("image",
                    action="store", type=str,
                    help="image to textify")
parser.add_argument("-s", "--size",
                    action="store", default=110, type=int, metavar="VALUE",
                    help="number of characters in a line (default: %(default)s)")
parser.add_argument("-c", "--cutoff",
                    action="store", default=3, type=int, metavar="VALUE",
                    help="histogram pixel cutoff percentage (default: %(default)s)")
parser.add_argument("-q", "--quantize",
                    action="store", default=255, type=int, metavar="VALUE",
                    help="number of colors to quantize the image into (default: %(default)s)")
parser.add_argument("-t", "--text",
                    action="store", type=argparse.FileType('w'), dest="output_text", metavar="FILE",
                    help="text output file")
parser.add_argument("-i", "--image",
                    action="store", type=str, dest="output_image", metavar="FILE",
                    help="image output file")

parser.add_argument("--invert",
                    action="store_true",
                    help="invert the provided image")
parser.add_argument("--white-bg",
                    action="store_true",
                    help="use white background for output image (use black color for text)")
parser.add_argument("--transparent",
                    action="store_true",
                    help="make a transparent output image")
parser.add_argument("--chars",
                    action="store", default=" `~!sTomN@", type=list, metavar="STRING",
                    help="ascii character list to use (default: '%(default)s')")
# parser.add_argument("--image-size",
#                     action="store", nargs=2, type=int, metavar=("X", "Y"),
#                     help="force a specific size for the produced image")
parser.add_argument("--font-size",
                    action="store", default=12, type=int, metavar="VALUE",
                    help="font size for image output")
parser.add_argument("--line-spacing",
                    action="store", default=5, type=int, metavar="VALUE",
                    help="line spacing for image output (default: %(default)s)")
parser.add_argument("--font-face",
                    action="store", default="consola.ttf", type=str, metavar="TTF_FILE",
                    help="font face for image output (default: %(default)s)")
parser.add_argument("--y-shrink",
                    action="store", default=1.99999, type=float, metavar="VALUE",
                    help="input image y-axis shrink factor (default: %(default)s)")

parser.add_argument('--alt',
                    action='store_true',
                    help='use alternative font settings (for mac or linux)')

parsed_args = parser.parse_args()

IMAGE_FILE = parsed_args.image
SIZE = parsed_args.size
CONTRAST_CUTOFF = parsed_args.cutoff
QUANTIZE = parsed_args.quantize
TXT_OUTPUT = parsed_args.output_text
IMAGE_OUTPUT = parsed_args.output_image
INVERT = parsed_args.invert
WHITE_BG = parsed_args.white_bg
TRANSPARENT = parsed_args.transparent
CHARS = parsed_args.chars
# IMG_OUT_SIZE = parsed_args.image_size
FONT_SIZE = parsed_args.font_size
SPACING = parsed_args.line_spacing
FONT_FILE = parsed_args.font_face
Y_SHRINK = parsed_args.y_shrink
TEXT = ""

if parsed_args.alt:
    FONT_FILE = "font/Inconsolata-Regular.ttf"
    SPACING = 1
    Y_SHRINK = 2
    CHARS = " `~!1f2d@"

assert len(CHARS) > 1, "Specify at least 2 characters"

# DEFAULT VALUES:
# SIZE = 110
# CONTRAST_CUTOFF = 3
# QUANTIZE = 255
# INVERT = False
# WHITE_BG = False
# CHARS = " `~!sTomN@"
# IMG_OUT_SIZE = None
# FONT_SIZE = 12
# SPACING = 5
# FONT_FILE = "consola.ttf"
# Y_SHRINK = 1.956
# TEXT = ""

# print(parsed_args)


def resize(img, size=SIZE, y_shrink=Y_SHRINK):
    '''Returns a resized image

    The image height is changed to compensate with the
    height of the ascii characters so the image stays proportional
    when displayed as text

    :param image: image to resize (type: PIL image object).
    :return: image (type: PIL image object)
    '''
    aspect_ratio = img.width / img.height
    w = size
    h = w / aspect_ratio
    if y_shrink:
        h = round(h / y_shrink)
    else:
        h = round(h)
    # h = trunc((w * aspect_ratio) / y_shrink)
    return img.resize((w, h), resample=Image.BICUBIC)


def image_it(text, font_size=FONT_SIZE, spacing=SPACING, font_file=FONT_FILE, white_bg=WHITE_BG, transparent=TRANSPARENT):
    '''Returns an textified version of the original image

    :param: text: ascii data of the image.
    :param font_size: font size of the text.
    :param spacing: spacing between the multiline text.
    :param font_file: the ttf file of the font style to use.
    :return: image (type: PIL image object).
    '''
    from PIL import ImageDraw, ImageFont

    bg = 0
    tfill = 255
    if white_bg:
        bg, tfill = tfill, bg

    try:
        font = ImageFont.truetype(font_file, font_size)
    except:
        raise Exception(
            "Font not found. Check this link to resolve the error: https://github.com/millionhz/textify#resolving-the-font-issue")
    print("Getting Image Size")
    x, y = font.getsize_multiline(text, spacing=spacing)
    print("Rendering Image")

    if transparent:
        img_out = Image.new("RGBA", (x, y), color=(0, 0, 0, 0))
        if white_bg:
            tfill = (0, 0, 0, 255)
        else:
            tfill = (255, 255, 255, 255)
    else:
        img_out = Image.new("L", (x, y), color=bg)

    ImageDraw.Draw(img_out).multiline_text(
        (0, 0), text, fill=tfill, font=font, spacing=spacing)
    return img_out


################################ PROGRAM ################################

img = Image.open(IMAGE_FILE).convert("L")

ORIG_HEIGHT = img.height
ORIG_WIDTH = img.width

print(f"Input Image Aspect Ratio: {img.height/img.width}")

if INVERT:
    img = ImageChops.invert(img)

print("Resizing Image")
img = resize(img)

print("Adjusting Contrast")
img = ImageOps.autocontrast(img, cutoff=CONTRAST_CUTOFF)

if QUANTIZE < 150:
    print("Quantizing Color")
    img = img.quantize(QUANTIZE, method=1).convert("L")

print("Converting Image to ASCII")
# print(f"Chars: \"{''.join(CHARS)}\"")

# this will change all the values of the pixels to the
# indexes of the CHARS array. I am using the PIL.Image.point()
# as it is implemented in C which makes the program faster

img = img.point(lambda x: round(x/255*(len(CHARS)-1)))
for y in range(img.height):
    for x in range(img.width):
        TEXT += CHARS[img.getpixel((x, y))]
    TEXT += "\n"

TEXT = TEXT[:-2]

img.close()

if SIZE < 116:
    print(TEXT)
else:
    print("Image Too Large To Display On Console")

if TXT_OUTPUT:
    print("Making Text File")
    TXT_OUTPUT.writelines(TEXT)
    print(f"{TXT_OUTPUT.name} Saved")

if IMAGE_OUTPUT:
    print("Making Image File")

    img_out = image_it(TEXT)

    # if IMG_OUT_SIZE:
    #     print("Resizing Output Image")
    #     img_out = img_out.resize(tuple(IMG_OUT_SIZE), resample=Image.BICUBIC)

    print(f"Produced Image Aspect Ratio: {img_out.height/img_out.width}")

    img_out.save(IMAGE_OUTPUT)
    print(f"{IMAGE_OUTPUT} Saved")
