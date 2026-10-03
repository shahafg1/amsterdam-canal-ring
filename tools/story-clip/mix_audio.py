import subprocess, os
SFX=os.environ.get('SFX_DIR','sfx')   # folder of your own .mp3 sound effects (not included in this repo)
# (file, start seconds, volume)
EV=[('logo_hit',0.60,.55),
    ('ar_whoosh',4.35,.50),('ui_pop',4.95,.55),('soft_tick',4.85,.55),
    ('soft_tick',6.00,.60),('soft_tick',6.90,.60),('soft_tick',8.10,.60),
    ('charge_up',7.40,.45),('launch',9.00,.60),('soft_tick',10.20,.5),('chime',10.80,.55),
    ('ui_whoosh',11.30,.55),('soft_thump',12.00,.60),
    ('ui_pop',12.15,.50),
    ('ar_whoosh',14.15,.35),('ui_pop',14.55,.50),
    ('ar_whoosh',15.95,.35),('ui_pop',16.35,.50),
    ('ar_whoosh',17.75,.35),('ui_pop',18.15,.50),
    ('ar_whoosh',19.55,.35),('launch',19.80,.50),('ui_pop',19.95,.45),
    ('ar_whoosh',21.40,.40),('logo_hit',21.60,.50),('glass_ting',22.45,.55),('ui_pop',22.95,.50)]
cmd=['ffmpeg','-v','error','-y','-i','music.wav']
for f,_,_ in EV: cmd+=['-i',f'{SFX}/{f}.mp3']
fl=['[0:a]volume=1.0[m]']
for i,(f,t,v) in enumerate(EV,1):
    ms=int(t*1000); fl.append(f'[{i}:a]aformat=sample_rates=44100:channel_layouts=stereo,volume={v},adelay={ms}|{ms}[s{i}]')
fl.append('[m]'+''.join(f'[s{i}]' for i in range(1,len(EV)+1))+f'amix=inputs={len(EV)+1}:normalize=0:duration=first,atrim=0:25,afade=t=out:st=24.2:d=0.8,loudnorm=I=-14:TP=-1.5:LRA=11[o]')
cmd+=['-filter_complex',';'.join(fl),'-map','[o]','-ar','44100','-ac','2','mix.wav']
subprocess.run(cmd,check=True)
print('mix.wav ok')
