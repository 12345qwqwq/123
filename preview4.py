"""Static check of bystander.html BURN stage: fire ignited along a knife
scratch spreads outward on black, coloured by the same flamePool as before.
Ports FlameField's JS automaton to numpy for one mid-spread frame."""
import numpy as np, math, random
from PIL import Image, ImageDraw, ImageFilter
random.seed(2); np.random.seed(2)
W,H=1180,700
GW=172; GH=max(8,round(GW*H/W))
SMOLDER,SMOLDER_GROW,FIRE_GROW,CONSUME,DIE=0.30,0.55,2.4,2.6,3.0
IGNITE_THRESH,SEED,CATCH=0.52,0.05,0.34

fire=np.zeros((GH,GW)); fuel=np.ones((GH,GW))
# ignite along a diagonal scratch
pts=[]
for i in range(40):
    x=0.22+0.5*i/40+0.05*math.sin(i/5); y=0.25+0.5*i/40
    pts.append((x,y))
for (fx,fy) in pts:
    gx,gy=int(fx*GW),int(fy*GH); R=2
    for dy in range(-R,R+1):
        for dx in range(-R,R+1):
            x,y=gx+dx,gy+dy
            if 0<=x<GW and 0<=y<GH and dx*dx+dy*dy<=R*R: fire[y,x]=max(fire[y,x],SEED)

def shiftmax(a):
    m=a.copy()
    m[:,1:]=np.maximum(m[:,1:],a[:,:-1]); m[:,:-1]=np.maximum(m[:,:-1],a[:,1:])
    m[1:,:]=np.maximum(m[1:,:],a[:-1,:]); m[:-1,:]=np.maximum(m[:-1,:],a[1:,:])
    return m
dt=1/60
for _ in range(220):  # ~3.7s
    mn=shiftmax(fire)
    catch=(fuel>0)&(fire<1e-4)&(mn>IGNITE_THRESH)
    fire=np.where(catch,CATCH,fire)
    active=fire>0
    rate=np.where(fire<SMOLDER,SMOLDER_GROW,FIRE_GROW)
    fire=np.where(active,np.minimum(1,fire+rate*dt),fire)
    fuel=np.where(active,fuel-CONSUME*fire*dt,fuel)
    burned=fuel<=0
    fuel=np.where(burned,0,fuel)
    fire=np.where(burned&active,np.maximum(0,fire-DIE*dt),fire)

# colour via flamePool
stops=np.array([[.16,.07,.02],[.37,.12,.02],[.70,.27,.04],[1,.48,.12],[1,.76,.36],[1,.94,.78]])
def pool(e):
    e=np.clip(e,0,1); t=e*5; i=np.clip(t.astype(int),0,4); f=(t-i)[...,None]
    return stops[i]*(1-f)+stops[i+1]*f
# upscale fire to full res
fimg=Image.fromarray((np.clip(fire,0,1)*255).astype(np.uint8)).resize((W,H),Image.BILINEAR)
fa=np.asarray(fimg,dtype=float)/255.0
e=np.clip(fa*1.25,0,1)
col=pool(e)
alpha=np.clip((e-0.05)/0.25,0,1)

out=np.zeros((H,W,3))  # black page
# scratches
scr=Image.new("L",(W,H),0); sd=ImageDraw.Draw(scr)
for i in range(len(pts)-1):
    x0,y0=pts[i][0]*W,pts[i][1]*H; x1,y1=pts[i+1][0]*W,pts[i+1][1]*H
    sd.line([(x0,y0),(x1,y1)],fill=70,width=2)
scra=np.asarray(scr,dtype=float)/255.0
out+=scra[...,None]*np.array([0.32,0.33,0.36])
# additive flame
out=out+col*alpha[...,None]
out=np.clip(out,0,1)
img=Image.fromarray((out*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.5))
# knife at scratch end
d=ImageDraw.Draw(img); ex,ey=pts[-1][0]*W,pts[-1][1]*H
d.polygon([(ex,ey),(ex-7,ey-34),(ex,ey-46),(ex+5,ey-34)],fill=(233,239,246))
d.rectangle([ex-3,ey,ex+3,ey+15],fill=(58,42,26))
img.save("preview4.png"); print("wrote preview4.png  burned%%=%.2f"%(1-fuel.mean()))
