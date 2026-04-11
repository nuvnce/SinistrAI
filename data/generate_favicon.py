from PIL import Image, ImageDraw, ImageFont
import os

img  = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Fond bleu arrondi
draw.rounded_rectangle([0, 0, 63, 63], radius=14, fill=(37, 99, 235, 255))

# Bouclier simplifié
draw.polygon([(32,8),(56,20),(56,38),(32,56),(8,38),(8,20)], fill=(255,255,255,220))
draw.polygon([(32,16),(50,26),(50,40),(32,52),(14,40),(14,26)], fill=(37,99,235,255))
draw.text((24, 22), "S", fill=(255,255,255,255))

output = os.path.join(os.path.dirname(__file__), '..', 'app', 'static', 'img', 'favicon.png')
img.save(output)
print("✅ Favicon généré !")