from PIL import Image, ImageOps


def image_get_size(image_path):
    ext = image_path.split('.')[-1]
    if ext not in ['jpg', 'jpeg', 'png']:
        return 0
    img = Image.open(image_path)
    img = ImageOps.exif_transpose(img)
    width, height = img.size
    return [width, height]


def image_resize(image_path, base_width=2000, up_scale=False, return_size=False, base_size=None):
    ext = image_path.split('.')[-1]
    if ext not in ['jpg', 'jpeg', 'png']:
        return (image_path, []) if return_size else image_path

    img = Image.open(image_path)
    img = ImageOps.exif_transpose(img)

    width, height = img.size

    if base_size is not None:
        if max(width, height) <= base_size and not up_scale:
            return (image_path, [width, height]) if return_size else image_path

        if width >= height:
            target_width = base_size
            target_height = int(height * (target_width / width))
        else:
            target_height = base_size
            target_width = int(width * (target_height / height))
    else:
        if width <= base_width and not up_scale:
            return (image_path, [width, height]) if return_size else image_path
        w_percent = base_width / float(width)
        target_width = base_width
        target_height = int(height * w_percent)

    output_path = image_path.replace('.' + ext, '_resized.' + ext)
    img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
    img.save(output_path, subsampling=0, quality=92)

    return (output_path, [target_width, target_height]) if return_size else output_path


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
