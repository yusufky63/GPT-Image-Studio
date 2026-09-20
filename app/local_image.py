from PIL import Image,ImageOps
from pathlib import Path
from .config import IMAGE_DIR
import time

def resize_or_crop(source,size,mode="Fit",output_dir=None):
    w,h=map(int,size.split("x")); im=Image.open(source).convert("RGBA")
    if mode=="Crop":
        out=ImageOps.fit(im,(w,h),method=Image.Resampling.LANCZOS)
    elif mode=="Stretch":
        out=im.resize((w,h),Image.Resampling.LANCZOS)
    else:
        contained=ImageOps.contain(im,(w,h),method=Image.Resampling.LANCZOS)
        out=Image.new("RGBA",(w,h),(0,0,0,0)); out.alpha_composite(contained,((w-contained.width)//2,(h-contained.height)//2))
    dest=Path(output_dir) if output_dir else IMAGE_DIR; dest.mkdir(parents=True,exist_ok=True)
    p=dest/f"{time.strftime('%Y-%m-%d_%H-%M-%S')}_local_{w}x{h}.png"; out.save(p)
    return str(p)
