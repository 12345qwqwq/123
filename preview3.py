"""Static sanity-check of bystander.html's BURN compositing: a dark letter
portrait painted with knife strokes -> charred-ring holes revealing the
vintage paper beneath. Mirrors BurnField.stamp/composite. Not the deliverable."""
import math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
random.seed(5)
W,H=1180,720

def font(opts,sz):
    for p in opts:
        try: return ImageFont.truetype(p,sz)
        except: pass
    return ImageFont.load_default()
MONO=["/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]

# paper
paper=Image.new("RGB",(W,H))
pd=ImageDraw.Draw(paper)
for y in range(H):
    t=y/H; pd.line([(0,y),(W,y)],fill=(int(239*(1-t)+217*t),int(231*(1-t)+201*t),int(210*(1-t)+164*t)))

# portrait stand-in: cold navy field + light letter speckle
port=Image.new("RGBA",(W,H),(7,9,18,255))
ptd=ImageDraw.Draw(port)
gf=font(MONO,13)
import string
for gy in range(0,H,17):
    for gx in range(0,W,11):
        v=random.randint(30,200); c=(int(v*0.6),int(v*0.8),v)
        ptd.text((gx,gy),random.choice(string.ascii_letters),font=gf,fill=(c[0],c[1],c[2],255))
# radial top glow
glow=Image.new("RGBA",(W,H),(0,0,0,0)); gd=ImageDraw.Draw(glow)
gd.ellipse([W*0.2,-H*0.3,W*0.8,H*0.5],fill=(60,90,130,60)); port=Image.alpha_composite(port,glow)

# char + burn(hole) layers
char=Image.new("RGBA",(W,H),(0,0,0,0)); cd=ImageDraw.Draw(char)
hole=Image.new("L",(W,H),0); hd=ImageDraw.Draw(hole)
blade=44
def stamp(x,y):
    rh,rc=blade*0.72,blade*1.18
    # char ring (transparent center, dark rim)
    ring=Image.new("RGBA",(W,H),(0,0,0,0)); rd=ImageDraw.Draw(ring)
    steps=24
    for i in range(steps,0,-1):
        rr=rc*i/steps
        if rr<rh*0.45: a=0
        elif rr<rh: a=int(150*(rr-rh*0.45)/(rh*0.55))
        else: a=int(220*max(0,1-(rr-rh)/(rc-rh)))
        rd.ellipse([x-rr,y-rr,x+rr,y+rr],fill=(26,15,6,a))
    char.alpha_composite(ring)
    # hole (erase mask)
    hm=Image.new("L",(W,H),0); hmd=ImageDraw.Draw(hm)
    for i in range(16,0,-1):
        rr=rh*1.15*i/16; a=int(240*max(0,1-(rr/(rh*1.15))**1.5))
        hmd.ellipse([x-rr,y-rr,x+rr,y+rr],fill=a)
    from PIL import ImageChops
    return hm

# a curved knife stroke across the face
pts=[(W*0.30+math.sin(i/6)*70, H*0.30+i*9) for i in range(34)]
hacc=Image.new("L",(W,H),0)
from PIL import ImageChops
for (x,y) in pts:
    hm=stamp(x,y); hacc=ImageChops.lighter(hacc,hm)
hole=hacc

# composite: paper -> char -> portrait with holes
out=paper.convert("RGBA")
out.alpha_composite(char)
port_holes=port.copy(); port_holes.putalpha(ImageChops.subtract(port.getchannel("A"),hole))
out.alpha_composite(port_holes)
out=out.convert("RGB")

# knife at stroke end
od=ImageDraw.Draw(out); ex,ey=pts[-1]
od.polygon([(ex,ey),(ex-7,ey-34),(ex,ey-46),(ex+5,ey-34)],fill=(225,238,255))
od.rectangle([ex-3,ey,ex+3,ey+15],fill=(42,28,18))
# a few embers
for _ in range(40):
    x=ex+random.uniform(-30,30); y=ey-random.uniform(0,60); s=random.randint(1,3)
    c=random.choice([(207,234,255),(159,216,255),(255,176,102)])
    od.ellipse([x-s,y-s,x+s,y+s],fill=c)
out=out.filter(ImageFilter.GaussianBlur(0.4))
out.save("preview3.png"); print("wrote preview3.png")
