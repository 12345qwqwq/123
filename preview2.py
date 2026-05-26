"""Static sanity-check of part2.html's burn composite (one mid-burn frame).
Mirrors the GLSL: cover (PART TWO paper) eaten by a noisy radial flame ring,
revealing the ash-toned content page beneath. Not the deliverable -- the real
piece is interactive WebGL; this just verifies the look on a browserless box."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

random.seed(3); np.random.seed(3)
W, H = 1280, 800

def font(path_opts, sz):
    for p in path_opts:
        try: return ImageFont.truetype(p, sz)
        except: pass
    return ImageFont.load_default()
SERIF = ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"]
MONO  = ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]

def fbm_field(scale, seed):
    rng=np.random.default_rng(seed)
    small=rng.random((int(H/scale)+2,int(W/scale)+2))
    img=Image.fromarray((small*255).astype(np.uint8)).resize((W,H),Image.BICUBIC)
    return np.asarray(img,dtype=float)/255.0

# ---- cover page: cream paper + PART TWO ----
cover=Image.new("RGB",(W,H))
cd=ImageDraw.Draw(cover)
for y in range(H):
    t=y/H; r=int(239*(1-t)+217*t); g=int(231*(1-t)+201*t); b=int(210*(1-t)+164*t)
    cd.line([(0,y),(W,y)],fill=(r,g,b))
big=font(SERIF,210); small=font(MONO,30)
cd.text((W/2,H*0.40),"PART",font=big,fill=(28,20,12),anchor="mm")
cd.text((W/2,H*0.40+190),"TWO",font=big,fill=(28,20,12),anchor="mm")
cd.text((W/2,H*0.40+300),"B Y S T A N D E R   ·   N O. 17",font=small,fill=(40,28,16),anchor="mm")
cover_a=np.asarray(cover,dtype=float)/255.0

# ---- content page: aged paper + a few justified-ish lines ----
content=Image.new("RGB",(W,H),(230,220,194))
nd=ImageDraw.Draw(content)
body=font(MONO,17)
STORY=("You are number seventeen at the home for the disabled. A single sweet, "
"once, undid the whole of your life. The man crouched down. The wrapper turned "
"between his fingers, and the sun broke a small rainbow across it. You reached "
"out your hand. Then the basement. Very small. The air damp and mouldy, like a "
"coffin measured in advance to fit you. The bare bulb buzzed overhead, white and "
"scalding, and seared the tears from your eyes.").split()
boxX=int(W*0.085); boxW=W-2*boxX; cw=body.getlength("M"); sp=cw
y=80; line=[]; lw=0
def flush(words,last):
    global y
    if not words: return
    nat=sum(body.getlength(w) for w in words)+sp*(len(words)-1)
    gap=sp if (last or len(words)<2) else sp+(boxW-nat)/(len(words)-1)
    x=boxX
    for w in words:
        nd.text((x,y),w,font=body,fill=(36,26,16)); x+=body.getlength(w)+gap
    y+=int(17*1.62)
for w in STORY:
    add=(sp if line else 0)+body.getlength(w)
    if line and lw+add>boxW: flush(line,False); line=[]; lw=0
    line.append(w); lw+=(sp if len(line)>1 else 0)+body.getlength(w)
flush(line,True)
content_a=np.asarray(content,dtype=float)/255.0

# ---- burn field (mirror shader) ----
xs=np.linspace(0,1,W); ys=np.linspace(0,1,H); U,V=np.meshgrid(xs,ys)
aspect=W/H
cx,cy=0.46,0.46
d=np.sqrt(((U-cx)*aspect)**2+(V-(cy))**2)
nz=(fbm_field(60,1)+0.5*fbm_field(28,2)+0.25*fbm_field(13,3))/1.75
progress=0.62
b=progress-(d+(nz-0.5)*0.34)
T_FLAME,T_THROUGH=0.0,0.055

def pool(e):
    e=np.clip(e,0,1)
    stops=np.array([[.16,.07,.02],[.37,.12,.02],[.70,.27,.04],[1,.48,.12],[1,.76,.36],[1,.94,.78]])
    t=e*5; i=np.clip(t.astype(int),0,4); f=(t-i)[...,None]
    return stops[i]*(1-f)+stops[i+1]*f

ASH=np.array([0.10,0.075,0.05])
col=cover_a.copy()
# flame edge
edge=(b>=T_FLAME)&(b<T_THROUGH)
e=((b-T_FLAME)/(T_THROUGH-T_FLAME))
fire=pool(e)
k=np.clip((e-0.0)/0.22,0,1)[...,None]
col=np.where(edge[...,None], cover_a*(1-k)+fire*k, col)
# burned through -> content (ash near frontier)
through=b>=T_THROUGH
scorch=np.clip(1-(b-T_THROUGH)/0.10,0,1)[...,None]
revealed=content_a*(1-scorch*0.9)+ASH*(scorch*0.9)
col=np.where(through[...,None], revealed, col)
# ring glow
ring=np.exp(-((b-0.025)/0.05)**2)
glow=np.array([1,0.5,0.15])
col=np.clip(col+glow*(ring*0.35)[...,None]*(((b>T_FLAME-0.06)&(b<T_THROUGH+0.02))[...,None]),0,1)

out=Image.fromarray((col*255).astype(np.uint8))
# a few blue embers along the ring
od=ImageDraw.Draw(out,"RGBA")
ember=[(207,234,255),(159,216,255),(111,176,255),(127,208,255)]
for _ in range(120):
    a=random.random()*6.283; rr=progress*H*(0.85+random.random()*0.2)
    x=cx*W+math.cos(a)*rr; yy=cy*H+math.sin(a)*rr - random.random()*40
    if 0<x<W and 0<yy<H:
        c=random.choice(ember); s=random.randint(1,3)
        od.ellipse([x-s,yy-s,x+s,yy+s],fill=(c[0],c[1],c[2],200))
out=out.filter(ImageFilter.GaussianBlur(0.4))
out.save("preview2.png"); print("wrote preview2.png")
