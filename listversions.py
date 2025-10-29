#!/usr/bin/python3
import sys, os, glob
ROOT='.versiondir'
if len(sys.argv)!=2: sys.exit(1)
fn=sys.argv[1]
pairs=[]
for p in glob.glob(os.path.join(ROOT,f'{fn}.*')):
    try: pairs.append((int(p.rsplit('.',1)[-1]),p))
    except: pass
pairs.sort()
for n,_ in pairs:
    print(f'{fn}.{n}')