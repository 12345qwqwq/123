"""Static preview of BYSTANDER · Part II.
Reimplements the WebGL composite (background art + paper title + metaball
ember + char/burn-through + story) on the CPU so we can emit a PNG, since
this container has no browser to run the real interactive page."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

random.seed(7); np.random.seed(7)
W, H = 1280, 800

# ---------- value-noise fbm (matches the shader) ----------
def _hash(ix, iy):
    return (np.sin(ix*127.1 + iy*311.7) * 43758.5453) % 1.0
def noise(x, y):
    ix, iy = np.floor(x), np.floor(y)
    fx, fy = x-ix, y-iy
    ux, uy = fx*fx*(3-2*fx), fy*fy*(3-2*fy)
    a=_hash(ix,iy); b=_hash(ix+1,iy); c=_hash(ix,iy+1); d=_hash(ix+1,iy+1)
    return (a*(1-ux)+b*ux)*(1-uy) + (c*(1-ux)+d*ux)*uy
def fbm(x, y):
    v=np.zeros_like(x); amp=0.5
    for _ in range(5):
        v += amp*noise(x,y); x*=2; y*=2; amp*=0.5
    return v

# normalized coords
xs = np.linspace(0,1,W); ys = np.linspace(0,1,H)
U, V = np.meshgrid(xs, ys)
t = 1.2

# ---------- background painterly art (image-1 vibe) ----------
qx = U + 0.18*fbm(U*2+t*0.02, V*2+t*0.02)
qy = V + 0.18*fbm(U*2+5.2-t*0.02, V*2+5.2-t*0.02)
n = fbm(qx*3, qy*3); m = fbm(qx*1.3+2, qy*1.3+2); w = fbm(qx*5+10, qy*5+10)
def mix(a,b,k): return a*(1-k[...,None])+b*k[...,None]
def ss(e0,e1,x): return np.clip((x-e0)/(e1-e0),0,1)
darkred=np.array([0.16,0.0,0.02]); red=np.array([0.55,0.03,0.05])
blue=np.array([0.09,0.13,0.78]); white=np.array([0.93,0.93,0.97])
bg = np.broadcast_to(darkred,(H,W,3)).copy()
bg = mix(bg, red,  ss(0.30,0.72,n))
bg = mix(bg, blue, ss(0.58,0.92,m))
bg = mix(bg, white,ss(0.80,0.97,w)*0.85)
bg *= (0.45+0.70*ss(0.1,0.85,n))[...,None]

# ---------- story text baked onto a transparent layer ----------
STORY = ["You are No. 17 of the home for the disabled.",
"A single piece of candy in childhood undid everything.","",
"The man crouched down. The wrapper turned between his fingers,",
"sunlight breaking a small rainbow across it. You reached out.","",
"Then the basement. Very small. The air damp and mouldy —",
"like a coffin measured, in advance, to fit you.",
"The bulb buzzed overhead, white and scalding,",
"searing tears from your eyes. You thought that was the worst.","",
"When the acid landed on your face you learned what worst meant.",
"The pain was nearly death; you screamed, and the sound",
"bounced back and forth off the concrete walls.","",
"Your mind blurred. You remembered the butterfly in the textbook —",
"the caterpillar melts, burns, and sloughs away inside, in agony.",
"And your ending would not even be beauty.","",
"He watched you, a sculptor studying an unfinished work.",
"But his purpose was ruin.",
"The knife-tip pressed to skin.","",
"He set you by the roadside. Cardboard, the words neat:",
"“Born disabled, no one to lean on — kind soul, please help.”",
"You could not make a sound. Coins fell. Clink. Clink.",
"Someone said “what a poor child,” and walked away.","",
"— Who are you?"]
story_img = Image.new("RGBA",(W,H),(0,0,0,0)); sd=ImageDraw.Draw(story_img)
try: font_s=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",16)
except: font_s=ImageFont.load_default()
lh=24; y0=(H-len(STORY)*lh)//2
for i,l in enumerate(STORY):
    sd.text((int(W*0.09)+1,y0+i*lh+1), l, font=font_s, fill=(0,0,0,200))
    sd.text((int(W*0.09),y0+i*lh), l, font=font_s, fill=(244,238,232,235))
story_arr=np.asarray(story_img).astype(float)/255.0
bg = bg*(1-story_arr[...,3:4]) + story_arr[...,:3]*story_arr[...,3:4]

# ---------- paper + scratchy title ----------
paper_img = Image.new("RGB",(W,H),(239,233,224))
pa=np.asarray(paper_img).astype(float)
pa += (np.random.rand(H,W,1)-0.5)*18
pd_img=Image.fromarray(np.clip(pa,0,255).astype(np.uint8)); pd=ImageDraw.Draw(pd_img)
def best_font(sz):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"]:
        try: return ImageFont.truetype(p,sz)
        except: pass
    return ImageFont.load_default()
def scratch(txt, cy, sz):
    f=best_font(sz)
    bb=pd.textbbox((0,0),txt,font=f); tw=bb[2]-bb[0]
    x=(W-tw)//2
    for k in range(5):
        jx=int((random.random()-0.5)*sz*0.05); jy=int((random.random()-0.5)*sz*0.05)
        pd.text((x+jx,cy+jy),txt,font=f,fill=(20,16,15,int((0.22+k*0.06)*255)))
scratch("BYSTANDER", int(H*0.40), 120)
scratch("PART  II", int(H*0.585), 44)
paper=np.asarray(pd_img).astype(float)/255.0
# dry-ink speckle erosion
mask_dark=(paper.mean(axis=2)<0.35)&(np.random.rand(H,W)<0.30)
paper[mask_dark]=np.array([239,233,224])/255.0

# ---------- metaball ember field + burn ----------
px=U*W; py=V*H
balls=[(W*0.40,H*0.46,90),(W*0.46,H*0.44,55),(W*0.35,H*0.52,48),(W*0.50,H*0.50,40)]
field=np.zeros((H,W))
for bx,by,r in balls:
    d2=(px-bx)**2+(py-by)**2
    field += (r*r)/(d2+1.0)
# burn footprint baked as a soft trail the ember has already crossed
burn=np.zeros((H,W))
trail=[(W*0.18,H*0.55),(W*0.27,H*0.50),(W*0.34,H*0.49),(W*0.40,H*0.46)]
for bx,by in trail:
    d2=(px-bx)**2+(py-by)**2
    burn=np.maximum(burn, np.clip(1.3-d2/(95**2),0,1))
burn=np.maximum(burn, np.clip(ss(0.75,1.6,field),0,1))

hole=ss(0.50,0.72,burn); char=ss(0.10,0.50,burn)*(1-hole)
grain=fbm(px*0.06,py*0.06)
charcol=mix(np.array([0.34,0.19,0.07]),np.array([0.03,0.02,0.02]),ss(0.28,0.55,burn+grain*0.12))
col=paper.copy()
col=mix(col,charcol,char)
col=mix(col,bg,hole)
scorch=ss(0.02,0.14,burn)*(1-ss(0.14,0.30,burn))
col=mix(col,col*np.array([1.15,0.85,0.6]),scorch*0.6)
# live flame
glow=ss(0.45,1.0,field); core=ss(1.1,3.0,field)
flame=mix(np.array([1.0,0.45,0.18]),np.array([1.0,0.96,0.82]),core)
col += flame*glow[...,None]
col=np.clip(col,0,1)

out=Image.fromarray((col*255).astype(np.uint8))
out.save("preview.png")
print("wrote preview.png", out.size)
