"""Check the new acid-melt finale: white text snapshot -> column drip down
+ blur + teal multiply tint (mirrors Melt.render / the uploaded part2 melt)."""
import math, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
W,H=1000,640
def font(opts,sz):
    for p in opts:
        try: return ImageFont.truetype(p,sz)
        except: pass
    return ImageFont.load_default()
MONO=["/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]
# text snapshot (sparse remaining + the protected phrase), white on black
snap=Image.new("RGB",(W,H),(5,5,5)); d=ImageDraw.Draw(snap); f=font(MONO,17)
lines=["the burning was still printed deep inside your head",
       "your arms had no strength   your mouth had no words",
       "in the stacked coins   blurred   a face",
       "Who are you?"]
for i,l in enumerate(lines):
    d.text((90,150+i*70),l,font=f,fill=(242,242,238))
# melt at k
k=0.62; strip=3; dpr=1
buf=Image.new("RGB",(W,H),(5,5,5))
src=snap.load()
drop=k*k*H*0.55
cols=[0.5+0.34*math.sin(i*0.06)+0.18*math.sin(i*0.021+1.3) for i in range(W//strip+1)]
for i in range(W//strip):
    x=i*strip; dy=int(drop*(0.55+0.45*cols[i])); wob=int(math.sin(x*0.02)*3*k)
    region=snap.crop((x,0,x+strip,H))
    buf.paste(region,(max(0,x+wob),dy))
buf=buf.filter(ImageFilter.GaussianBlur(k*5))
# fade + teal tint (multiply)
out=Image.blend(Image.new("RGB",(W,H),(5,5,5)), buf, 1-k*0.5)
teal=Image.new("RGB",(W,H),(134,255,186))
out=ImageChops.multiply(out, Image.blend(Image.new("RGB",(W,H),(255,255,255)), teal, k*0.55))
out.save("preview6.png"); print("wrote preview6.png")
