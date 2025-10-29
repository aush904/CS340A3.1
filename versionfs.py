#!/usr/bin/python3
import os, sys, stat, time, errno, glob, shutil, filecmp
from fuse import FUSE, FuseOSError, Operations, LoggingMixIn

VERSION_ROOT = '.versiondir'
MAX_VERSIONS = 6

def ensure_version_root():
    if not os.path.exists(VERSION_ROOT):
        os.mkdir(VERSION_ROOT)

def is_visible_name(name):
    b = os.path.basename(name)
    return not b.startswith('.')

def logical_name(path):
    return os.path.basename(path)

def vpath(filename, n=1):
    return os.path.join(VERSION_ROOT, f'{filename}.{n}')

def existing_versions(filename):
    pat = os.path.join(VERSION_ROOT, f'{filename}.*')
    items = []
    for p in glob.glob(pat):
        try:
            n = int(p.rsplit('.', 1)[-1])
            items.append((n, p))
        except:
            pass
    items.sort()
    return items

def rotate_versions(filename):
    items = existing_versions(filename)
    if items:
        for n, p in reversed(items):
            if n == MAX_VERSIONS:
                try:
                    os.remove(p)
                except:
                    pass
            else:
                os.rename(p, vpath(filename, n + 1))

def files_equal(a, b):
    if not os.path.exists(a) or not os.path.exists(b):
        return False
    if os.path.getsize(a) != os.path.getsize(b):
        return False
    return filecmp.cmp(a, b, shallow=False)

class VersionFS(LoggingMixIn, Operations):
    def __init__(self):
        ensure_version_root()
        self.staging = {}

    def readdir(self, path, fh):
        ensure_version_root()
        if path != '/':
            yield '.'
            yield '..'
            return
        yield '.'
        yield '..'
        names = set()
        for p in glob.glob(os.path.join(VERSION_ROOT, '*.*')):
            base = os.path.basename(p)
            parts = base.split('.')
            if len(parts) < 2:
                continue
            filename = '.'.join(parts[:-1])
            if not is_visible_name(filename):
                continue
            if os.path.exists(vpath(filename, 1)):
                names.add(filename)
        for e in sorted(names):
            yield e

    def getattr(self, path, fh=None):
        ensure_version_root()
        if path == '/':
            now = int(time.time())
            mode = stat.S_IFDIR | 0o755
            return dict(st_mode=mode, st_nlink=2, st_size=0, st_ctime=now, st_mtime=now, st_atime=now)
        name = logical_name(path)
        if not is_visible_name(name):
            raise FuseOSError(errno.ENOENT)
        backing = vpath(name, 1)
        if not os.path.exists(backing):
            raise FuseOSError(errno.ENOENT)
        st = os.lstat(backing)
        return dict(st_mode=stat.S_IFREG | 0o644, st_nlink=1, st_size=st.st_size, st_ctime=st.st_ctime, st_mtime=st.st_mtime, st_atime=st.st_atime)

    def open(self, path, flags):
        ensure_version_root()
        name = logical_name(path)
        p = vpath(name, 1)
        if not os.path.exists(p):
            raise FuseOSError(errno.ENOENT)
        fd = os.open(p, flags)
        return fd

    def create(self, path, mode, fi=None):
        ensure_version_root()
        name = logical_name(path)
        if not is_visible_name(name):
            raise FuseOSError(errno.EPERM)
        p = vpath(name, 1)
        if not os.path.exists(p):
            with open(p, 'wb'):
                pass
        fd = os.open(p, os.O_WRONLY)
        return fd

    def read(self, path, size, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, size)

    def _staging_path(self, name):
        ensure_version_root()
        return os.path.join(VERSION_ROOT, f'.staging.{name}')

    def write(self, path, data, offset, fh):
        name = logical_name(path)
        sp = self.staging.get(name)
        if not sp:
            sp = self._staging_path(name)
            if os.path.exists(vpath(name, 1)):
                shutil.copy2(vpath(name, 1), sp) if not os.path.exists(sp) else None
            else:
                with open(sp, 'wb'):
                    pass
            self.staging[name] = sp
        with open(sp, 'r+b') as f:
            f.seek(offset)
            f.write(data)
        return len(data)

    def flush(self, path, fh):
        name = logical_name(path)
        cur = vpath(name, 1)
        sp = self.staging.get(name)
        if sp and os.path.exists(sp):
            if not os.path.exists(cur) or not files_equal(cur, sp):
                rotate_versions(name)
                os.replace(sp, vpath(name, 1))
            else:
                os.remove(sp)
            self.staging.pop(name, None)
        try:
            os.fsync(fh)
        except:
            pass
        return 0

    def release(self, path, fh):
        try:
            os.close(fh)
        except:
            pass
        return 0

    def truncate(self, path, length, fh=None):
        name = logical_name(path)
        sp = self.staging.get(name)
        if not sp:
            sp = self._staging_path(name)
            if os.path.exists(vpath(name, 1)):
                shutil.copy2(vpath(name, 1), sp)
            else:
                with open(sp, 'wb'):
                    pass
            self.staging[name] = sp
        with open(sp, 'r+b') as f:
            f.truncate(length)

    def unlink(self, path):
        name = logical_name(path)
        for _, p in existing_versions(name):
            try:
                os.remove(p)
            except:
                pass
        sp = self.staging.get(name)
        if sp and os.path.exists(sp):
            try:
                os.remove(sp)
            except:
                pass
        self.staging.pop(name, None)

    def rename(self, old, new):
        oldn = logical_name(old)
        newn = logical_name(new)
        if not is_visible_name(oldn) or not is_visible_name(newn):
            raise FuseOSError(errno.EPERM)
        for n, p in existing_versions(oldn):
            os.rename(p, vpath(newn, n))
        osp = self.staging.get(oldn)
        if osp and os.path.exists(osp):
            nsp = self._staging_path(newn)
            os.rename(osp, nsp)
            self.staging[newn] = nsp
            self.staging.pop(oldn, None)

    def utimens(self, path, times=None):
        name = logical_name(path)
        p = vpath(name, 1)
        if os.path.exists(p):
            os.utime(p, times)

def main(mountpoint):
    FUSE(VersionFS(), mountpoint, foreground=True, nothreads=True)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('usage: python3 versionfs.py <mountpoint>')
        sys.exit(1)
    main(sys.argv[1])
