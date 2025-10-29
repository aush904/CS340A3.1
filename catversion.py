#!/usr/bin/python3
import sys, os
ROOT='.versiondir'
if len(sys.argv)!=3: sys.exit(1)
fn=sys.argv[1]; n=sys.argv[2]
p=os.path.join(ROOT,f'{fn}.{n}')
with open(p,'rb') as f:
    sys.stdout.buffer.write(f.read())