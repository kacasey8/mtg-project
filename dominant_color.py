from PIL import Image, ImageDraw

"""
This gets the dominant colors and outputs a visual to 'outfile.png'
Taken from https://gist.github.com/zollinger/1722663
"""

def get_colors(infile, outfile, numcolors=10, swatchsize=20, resize=150):
    image = Image.open(infile)
    image = image.resize((resize, resize))
    result = image.convert('P', palette=Image.ADAPTIVE, colors=10)
    result.putalpha(0)
    colors = result.getcolors(resize*resize)

    # Save colors to file

    pal = Image.new('RGB', (swatchsize*numcolors, swatchsize))
    draw = ImageDraw.Draw(pal)

    posx = 0
    for count, col in colors:
        draw.rectangle([posx, 0, posx+swatchsize, swatchsize], fill=col)
        posx = posx + swatchsize

    del draw
    pal.save(outfile, "PNG")

if __name__ == '__main__':
    get_colors('Sailboat-sunset.jpg', 'outfile.png')
