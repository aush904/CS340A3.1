#!/usr/bin/python3
import os, shutil, subprocess
try: subprocess.run(['fusermount','-u','mount'], check=False)
except: pass
if os.path.isdir('.versiondir'):
    shutil.rmtree('.versiondir', ignore_errors=True)
if os.path.isdir('mount'):
    shutil.rmtree('mount', ignore_errors=True)
