"""Recorte robusto: fondo = pixeles parecidos al fondo conectados al borde; el resto se rellena. Uso: cutout2.py in out [tol]"""
import sys, numpy as np
from PIL import Image
from scipy import ndimage as ndi
def cut(src,dst,tol=40):
    im=Image.open(src).convert("RGB"); a=np.asarray(im).astype(np.int16)
    b=np.concatenate([a[0],a[-1],a[:,0],a[:,-1]]); bg=np.median(b,axis=0)
    close=np.abs(a-bg).sum(2)<tol
    lab,_=ndi.label(close); e=set(np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]])))-{0}
    bgm=np.isin(lab,list(e))
    fg=ndi.binary_fill_holes(~bgm); fg=ndi.binary_opening(fg,iterations=2)
    l2,n=ndi.label(fg)
    if n>1:
        sz=ndi.sum(fg,l2,range(1,n+1)); keep=[i+1 for i,s in enumerate(sz) if s>0.002*fg.size]; fg=np.isin(l2,keep)
    al=ndi.gaussian_filter(fg.astype(float),1.0); al=np.clip((al-0.3)/0.4,0,1)
    Image.fromarray(np.dstack([np.asarray(im),(al*255).astype(np.uint8)]),"RGBA").save(dst)
if __name__=="__main__": cut(sys.argv[1],sys.argv[2],float(sys.argv[3]) if len(sys.argv)>3 else 40)
