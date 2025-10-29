#!/usr/bin/python3
import sys, os
ROOT='.versiondir'; MAX=6
if len(sys.argv)!=2: sys.exit(1)
fn=sys.argv[1]
for i in range(2,MAX+1):
    p=os.path.join(ROOT,f'{fn}.{i}')
    if os.path.exists(p):
        try: os.remove(p)
        except: pass
