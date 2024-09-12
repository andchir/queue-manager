from PIL import Image, ImageOps


def image_resize(image_path, base_width=2000, up_scale=False):
    img = Image.open(image_path)
    ext = image_path.split('.')[-1]
    if ext not in ['jpg', 'jpeg', 'png']:
        return image_path

    img = ImageOps.exif_transpose(img)

    width, height = img.size
    if width <= base_width and not up_scale:
        return image_path
    output_path = image_path.replace('.' + ext, '_resized.' + ext)
    w_percent = (base_width / float(width))
    h_size = int((float(height) * float(w_percent)))

    img = img.resize((base_width, h_size), Image.Resampling.LANCZOS)
    img.save(output_path, subsampling=0, quality=92)

    return output_path


def convert_to_jpg(image_path):
    ext = image_path.split('.')[-1]
    if ext in ['jpg', 'jpeg']:
        return image_path
    out_image_path = image_path.replace('.png', '.jpg').replace('.bmp', '.jpg')
    im = Image.open(image_path)
    rgb_im = im.convert('RGB')
    rgb_im.save(out_image_path, quality=96)
    return out_image_path


if __name__ == '__main__':
    image_path = '/home/andrew/PycharmProjects/queue-manager/uploads/output/final_results/ce814cca-685d-11ef-9ade-c7ac38affbec_resized.png'
    out_path = convert_to_jpg(image_path)
    print(out_path)
