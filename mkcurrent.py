#!/usr/bin/python3
import sys, os, shutil
ROOT='.versiondir'; MAX=6
if len(sys.argv)!=3: sys.exit(1)
fn=sys.argv[1]; k=int(sys.argv[2])
src=os.path.join(ROOT,f'{fn}.{k}')
if not os.path.exists(src): sys.exit(1)
tmp=os.path.join(ROOT,f'.tmp.{fn}')
shutil.copy2(src,tmp)
for i in range(MAX,1,-1):
    old=os.path.join(ROOT,f'{fn}.{i-1}')
    new=os.path.join(ROOT,f'{fn}.{i}')
    if os.path.exists(new):
        try: os.remove(new)
        except: pass
    if os.path.exists(old):
        os.rename(old,new)
dst=os.path.join(ROOT,f'{fn}.1')
if os.path.exists(dst): os.remove(dst)
os.rename(tmp,dst)
