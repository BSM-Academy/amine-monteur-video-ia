# Efface les restes violets (surlignage karaoké) laissés par Vmake dans la bande des sous-titres : interpolation verticale
import subprocess,sys,numpy as np
src,dst=sys.argv[1],sys.argv[2];W,H=720,1280;Y0,Y1=850,1110
# Garder la cadence exacte de la source (ex. 7381/250), sinon la durée change et l'image se décale de la voix
fps=subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=r_frame_rate','-of','csv=p=0',src],capture_output=True,text=True).stdout.strip() or '30'
dec=subprocess.Popen(['ffmpeg','-v','error','-i',src,'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',fps,'-i','-','-c:v','libx264','-crf','14','-pix_fmt','yuv420p',dst],stdin=subprocess.PIPE)
n=0;tot=0
while True:
    b=dec.stdout.read(W*H*3)
    if len(b)<W*H*3:break
    f=np.frombuffer(b,np.uint8).reshape(H,W,3).copy();z=f[Y0:Y1].astype(int);r,g,bl=z[...,0],z[...,1],z[...,2]
    m=(bl>85)&(bl-g>35)&(r-g>5)&(bl>r+10)
    if m.sum()>15:
        mm=m.copy()
        for dy in (-5,-4,-3,-2,-1,1,2,3,4,5):mm|=np.roll(m,dy,0)
        for dx in (-5,-4,-3,-2,-1,1,2,3,4,5):mm|=np.roll(mm,dx,1)
        zf=z.copy()
        for x in np.where(mm.any(0))[0]:
            col=mm[:,x];ys=np.where(~col)[0]
            if len(ys)<2:continue
            for c in range(3):zf[:,x,c]=np.where(col,np.interp(np.arange(len(col)),ys,z[ys,x,c]),z[:,x,c])
        f[Y0:Y1]=zf.astype(np.uint8);tot+=1
    enc.stdin.write(f.tobytes());n+=1
enc.stdin.close();enc.wait();print('images',n,'retouchées',tot)
