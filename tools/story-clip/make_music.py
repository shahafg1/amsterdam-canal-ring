"""Original 25 s soundtrack, 100 BPM (1 beat = 0.6 s), written as code with numpy only. Free, no samples, no licence."""
import numpy as np, wave
SR=44100; BEAT=0.6; DUR=25.0; N=int(SR*DUR)
rng=np.random.default_rng(7)
t=np.arange(N)/SR
mixL=np.zeros(N); mixR=np.zeros(N)       # tonal bed (gets sidechained)
drL=np.zeros(N); drR=np.zeros(N)         # drums / fx (not ducked)
fq=lambda m:440*2**((m-69)/12)

def put(bufL,bufR,sig,start,pan=0.5,gain=1.0):
    i=int(start*SR)
    if i>=N: return
    s=sig[:N-i]
    bufL[i:i+len(s)]+=s*gain*np.cos(pan*np.pi/2)
    bufR[i:i+len(s)]+=s*gain*np.sin(pan*np.pi/2)

def lp(x,k):      # moving-average lowpass
    return np.convolve(x,np.ones(k)/k,mode='same')

# ---- timeline / structure (seconds)
INTRO_END,CTRL_END,SHOW_END=4.8,12.0,21.6
def curve(pts):  return np.interp(t,[p[0] for p in pts],[p[1] for p in pts])
g_pad =curve([(0,0),(0.4,.55),(4.8,.65),(12,.7),(21.6,.75),(24,.8),(25,0)])
g_arp =curve([(0,0),(4.7,0),(4.8,.55),(10.8,.6),(12,.95),(21.6,.95),(21.7,.0),(25,0)])
g_bass=curve([(0,0),(4.7,0),(4.8,.8),(12,.95),(21.6,.95),(21.7,.7),(24.5,.7),(25,0)])

# ---- chords: one per bar (4 beats = 2.4 s)
CH={'Am':[45,57,60,64,67,71],'F':[41,53,57,60,64,67],'C':[48,55,60,64,67,71],'G':[43,50,55,59,62,69]}
BARS=['Am','F','C','G','Am','F','C','G','Am','F','C']     # bar k starts at 2.4*k
def bar_at(tm): return BARS[min(int(tm/(4*BEAT)),len(BARS)-1)]

# ---- pad
def pad_note(m,dur,detune):
    n=int((dur+0.9)*SR); tt=np.arange(n)/SR; f=fq(m)*(1+detune)
    w=sum(np.sin(2*np.pi*f*h*tt+h)*(1/h**1.4) for h in range(1,6))
    env=np.minimum(1,tt/0.55)**2*np.where(tt<dur,1,np.exp(-(tt-dur)*4.5))
    return w*env
for k,name in enumerate(BARS):
    st=k*4*BEAT
    if st>=DUR: break
    for j,m in enumerate(CH[name][1:5]):
        a=pad_note(m,4*BEAT,0.0025); b=pad_note(m,4*BEAT,-0.0025)
        put(mixL,mixR,a,st,0.2,0.05); put(mixL,mixR,b,st,0.8,0.05)
# ---- bass (root, syncopated: beat 1 and the "and" of 2)
def bass_note(m,dur):
    n=int(dur*SR); tt=np.arange(n)/SR; f=fq(m)
    w=np.sin(2*np.pi*f*tt)+0.35*np.sin(4*np.pi*f*tt)+0.12*np.sin(6*np.pi*f*tt)
    return w*np.minimum(1,tt/0.01)*np.exp(-tt*2.2)
for k in range(len(BARS)):
    st=k*4*BEAT; root=CH[BARS[k]][0]
    for off,d in ((0,1.4),(1.5*BEAT,0.9),(2*BEAT,1.1)):
        if st+off<DUR: put(mixL,mixR,bass_note(root,d),st+off,0.5,0.34)
# ---- plucks: 8th-note arpeggio, plus sparse bells in the intro and the outro
def pluck(m):
    n=int(1.0*SR); tt=np.arange(n)/SR; f=fq(m)
    w=np.sin(2*np.pi*f*tt)+0.5*np.sin(4*np.pi*f*tt)*np.exp(-tt*9)+0.22*np.sin(6*np.pi*f*tt)*np.exp(-tt*14)
    return w*np.exp(-tt*5.2)*(1-np.exp(-tt*600))
def bell(m,dur=2.2):
    n=int(dur*SR); tt=np.arange(n)/SR; f=fq(m)
    w=sum(a*np.sin(2*np.pi*f*r*tt)*np.exp(-tt*d) for a,r,d in ((1,1,1.6),(.45,2.76,2.6),(.25,5.4,4.0),(.15,8.93,6)))
    return w*(1-np.exp(-tt*800))
pat=[1,3,2,4,3,2,4,2]
for e in range(int(DUR/(BEAT/2))):
    tm=e*BEAT/2
    if INTRO_END<=tm<SHOW_END+0.001 and not (CTRL_END-1.2<=tm<CTRL_END and False):
        ch=CH[bar_at(tm)]; m=ch[pat[e%8]]+12
        put(mixL,mixR,pluck(m),tm,0.3+0.4*((e%3)/2),0.16*(1 if tm>=CTRL_END else .8))
for tm,name,m in ((0.6,'Am',81),(1.8,'Am',76),(3.0,'F',77),(4.2,'F',72)):   # intro bells
    put(mixL,mixR,bell(m),tm,0.35 if m%2 else 0.65,0.09)
for tm,m in ((21.6,76),(22.2,81),(22.8,84),(23.4,79)):                       # outro bells
    put(mixL,mixR,bell(m),tm,0.4,0.10)
mixL*=g_pad*0+1; mixR*=1       # (kept explicit)
# per-layer gains were baked in volumes above; apply the section curves to the bed as a whole
bed=curve([(0,.55),(4.8,.8),(12,1.0),(21.6,1.0),(23,.9),(24.5,.6),(25,0)])
mixL*=bed; mixR*=bed
# ---- drums
def kick():
    n=int(.4*SR); tt=np.arange(n)/SR; f=42+95*np.exp(-tt*30); ph=2*np.pi*np.cumsum(f)/SR
    return (np.sin(ph)*np.exp(-tt*8.5)+0.35*np.sin(2*ph)*np.exp(-tt*20))*np.minimum(1,tt/0.002)
def clap():
    n=int(.28*SR); tt=np.arange(n)/SR; x=rng.standard_normal(n); x=x-lp(x,6)
    env=sum(np.exp(-np.maximum(tt-d,0)*(110 if d<.03 else 26))*(tt>=d) for d in (0,.011,.022,.034))
    return x*env*0.5
def hat(open_=False):
    n=int((.25 if open_ else .05)*SR); tt=np.arange(n)/SR; x=rng.standard_normal(n); x=x-lp(x,3)
    return x*np.exp(-tt*(14 if open_ else 90))*0.5
def boom():
    n=int(1.6*SR); tt=np.arange(n)/SR; f=60*np.exp(-tt*1.3)+28
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*2.0)
kicks=[]
for b in range(int(DUR/BEAT)+1):
    tm=b*BEAT
    if INTRO_END<=tm<CTRL_END-0.01 and b%4 in (0,2) or (INTRO_END<=tm<CTRL_END-0.01 and b%4==3 and (b//4)%2==1): kicks.append(tm)
    elif CTRL_END<=tm<SHOW_END-0.01 and not (19.2<=tm<19.8 and False): kicks.append(tm)
kicks.append(CTRL_END)   # downbeat of the gameplay section
kicks.append(SHOW_END); kicks.append(SHOW_END+2*BEAT)
for tm in sorted(set(round(k,4) for k in kicks)):
    if tm<DUR: put(drL,drR,kick(),tm,0.5,0.95 if tm in (CTRL_END,SHOW_END) else 0.8)
for b in range(int(DUR/BEAT)+1):
    tm=b*BEAT
    if CTRL_END<=tm<SHOW_END-0.01 and b%2==1: put(drL,drR,clap(),tm,0.5,0.55)
for e in range(int(DUR/(BEAT/2))):
    tm=e*BEAT/2
    if INTRO_END+BEAT<=tm<SHOW_END-0.01: put(drL,drR,hat(e%4==3 and tm>=CTRL_END),tm,0.62 if e%2 else 0.38,0.16 if tm>=CTRL_END else 0.10)
# riser into the gameplay section (2 beats) and an impact on the downbeat
rs=10.8; rn=int((CTRL_END-rs)*SR); rt=np.arange(rn)/SR
sweep=np.sin(2*np.pi*np.cumsum(180+1500*(rt/(CTRL_END-rs))**2)/SR)*(rt/(CTRL_END-rs))**2*0.18
nz=rng.standard_normal(rn); nz=(nz-lp(nz,8))*(rt/(CTRL_END-rs))**2.5*0.22
put(drL,drR,sweep+nz,rs,0.5,1.0)
put(drL,drR,boom(),CTRL_END,0.5,0.9)
put(drL,drR,hat(True)*3,CTRL_END,0.5,0.5)
put(drL,drR,boom(),SHOW_END,0.5,0.75)
# intro swell
n=int(1.3*SR); tt=np.arange(n)/SR; sw=rng.standard_normal(n); sw=(sw-lp(sw,12))*(tt/1.3)**2*0.1
put(drL,drR,sw,0.0,0.5,1.0)
# ---- sidechain: the bed breathes with each kick
duck=np.ones(N)
for tm in sorted(set(kicks)):
    i=int(tm*SR)
    if i<N:
        seg=np.arange(min(int(.35*SR),N-i))/SR; duck[i:i+len(seg)]*=1-0.5*np.exp(-seg/0.11)
L=mixL*duck+drL; R=mixR*duck+drR
# ---- reverb (synthetic impulse, FFT convolution)
def reverb(x,amount=0.22,sec=1.6):
    n=int(sec*SR); tt=np.arange(n)/SR; ir=rng.standard_normal(n)*np.exp(-tt*3.2); ir=lp(ir,4)
    size=1<<int(np.ceil(np.log2(len(x)+n))); y=np.fft.irfft(np.fft.rfft(x,size)*np.fft.rfft(ir,size),size)[:len(x)]
    return x+y*amount*0.04
L=reverb(L);R=reverb(R)
# ---- master: gentle soft clip, fades, normalise
m=np.tanh(np.stack([L,R])*1.1)
fade=np.minimum(1,t/0.02)*np.minimum(1,(DUR-t)/1.4)
m*=fade; m/=np.max(np.abs(m))/0.89
pcm=(m.T*32767).astype('<i2')
with wave.open('music_raw.wav','wb') as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('wrote music_raw.wav', round(len(pcm)/SR,2),'s')
