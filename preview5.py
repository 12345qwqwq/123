"""Static check of the REVISED bystander.html flame: heat painted only along
the knife path (transient, decays behind the cursor) then coloured by the new
shader (ember->orange->white core + noisy edges). Confirms it stays local."""
import numpy as np, math, random
from PIL import Image, ImageDraw, ImageFilter
random.seed(4); np.random.seed(4)
W,H=1180,700
HW,HH=W//3,H//3
heat=np.zeros((HH,HW))
# knife path (a short stroke); recency -> heat (older points faded)
pts=[]
for i in range(46):
    x=0.30+0.40*i/46; y=0.52+0.16*math.sin(i/7)
    pts.append((x,y))
brush=30/W*HW
for k,(fx,fy) in enumerate(pts):
    recency=k/len(pts)            # newer points hotter (older decayed)
    amp=0.5*(0.25+0.75*recency)
    cx,cy=fx*HW,fy*HH
    yy,xx=np.ogrid[0:HH,0:HW]
    d=np.sqrt((xx-cx)**2+(yy-cy)**2)
    heat+=np.clip(1-d/brush,0,1)*amp
heat=np.clip(heat,0,1)
# upscale
himg=Image.fromarray((heat*255).astype(np.uint8)).resize((W,H),Image.BILINEAR)
ha=np.asarray(himg,float)/255.0
# noise
def fbm_field(scale,seed):
    rng=np.random.default_rng(seed); s=rng.random((H//scale+2,W//scale+2))
    return np.asarray(Image.fromarray((s*255).astype(np.uint8)).resize((W,H),Image.BICUBIC),float)/255.0
n=(fbm_field(40,1)+0.5*fbm_field(20,2))/1.5
f=np.clip(ha*1.4 - n*0.45,0,1)
glow=np.clip((f-0.045)/(0.55-0.045),0,1)
core=np.clip((f-0.62)/(0.95-0.62),0,1)
ember=np.array([0.55,0.10,0.02]); orange=np.array([1.0,0.42,0.12]); white=np.array([1.0,0.95,0.8])
t=np.clip(f/0.42,0,1)[...,None]
col=ember*(1-t)+orange*t
col=col*(1-core[...,None])+white*core[...,None]
alpha=glow
out=np.zeros((H,W,3))
# scratches
scr=Image.new("L",(W,H),0); sd=ImageDraw.Draw(scr)
for i in range(len(pts)-1):
    sd.line([(pts[i][0]*W,pts[i][1]*H),(pts[i+1][0]*W,pts[i+1][1]*H)],fill=70,width=2)
out+=(np.asarray(scr,float)/255.0)[...,None]*np.array([0.32,0.33,0.36])
out=np.clip(out+col*alpha[...,None],0,1)
img=Image.fromarray((out*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.4))
d=ImageDraw.Draw(img); ex,ey=pts[-1][0]*W,pts[-1][1]*H
d.polygon([(ex,ey),(ex-7,ey-34),(ex,ey-46),(ex+5,ey-34)],fill=(233,239,246)); d.rectangle([ex-3,ey,ex+3,ey+15],fill=(58,42,26))
img.save("preview5.png"); print("wrote preview5.png")
