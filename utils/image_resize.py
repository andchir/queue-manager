from PIL import Image


def image_resize(image_path, base_width=2000):
    img = Image.open(image_path)
    ext = image_path.split('.')[-1]
    if ext not in ['jpg', 'jpeg', 'png']:
        return image_path
    width, height = img.size
    if width <= base_width:
        return image_path
    output_path = image_path.replace('.' + ext, '_resized.' + ext)
    w_percent = (base_width / float(width))
    h_size = int((float(height) * float(w_percent)))
    img = img.resize((base_width, h_size), Image.Resampling.LANCZOS)
    img.save(output_path)

    return output_path
