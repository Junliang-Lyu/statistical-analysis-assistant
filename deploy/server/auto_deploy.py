"""Stats-only release puller. Default is verification-only; never targets other apps."""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path, PurePosixPath
from urllib.request import Request, urlopen

REPO='Junliang-Lyu/statistical-analysis-assistant'
BASE=Path('/opt/stats')
ID_PATTERN=r'\d{8}T\d{6}Z'


def validate_archive(path,rid):
    if not re.fullmatch(ID_PATTERN,rid): raise ValueError('Invalid release id')
    allowed={'compose.stats.yaml','stats.caddy','check-release.sh','release.txt',f'stats-api-{rid}.tar'}
    seen=set(); total=0
    with tarfile.open(path,'r:gz') as archive:
        for m in archive.getmembers():
            p=PurePosixPath(m.name)
            if p.is_absolute() or '..' in p.parts or '\\' in m.name or not p.parts or p.parts[0]!=rid:
                raise ValueError('Unexpected archive path')
            if m.isdir() and p.parts==(rid,): continue
            if not m.isfile() or len(p.parts)!=2 or p.parts[1] not in allowed or p.parts[1] in seen:
                raise ValueError('Unexpected archive member')
            total+=m.size
            if total>3_000_000_000: raise ValueError('Release is too large')
            seen.add(p.parts[1])
        if seen!=allowed: raise ValueError('Incomplete release')


def run(*args):
    return subprocess.run(args,check=True,capture_output=True,text=True).stdout.strip()


def fetch(url,target,limit):
    if not url.startswith(f'https://github.com/{REPO}/releases/download/'):
        raise ValueError('Unexpected release download location')
    with urlopen(url,timeout=120) as r, target.open('wb') as f:
        size=0
        while chunk:=r.read(1024*1024):
            size+=len(chunk)
            if size>limit: raise ValueError('Download exceeds limit')
            f.write(chunk)


def switch(rel,tag):
    state=BASE/'state'
    env=state/'release.env'
    rid=tag.removeprefix('release-')
    env.write_text(f'STATS_API_IMAGE=stats-api:{rid}\nSTATS_RELEASE={tag}\n')
    env.chmod(0o600)
    # Docker Compose injects the server-only private env_file; it is never printed here.
    cmd=['docker','compose','--project-name','stats','--env-file',str(env),'-f',str(rel/'compose.stats.yaml')]
    run(*cmd,'up','-d','--no-build','--pull','never','stats-api')
    run('bash',str(rel/'check-release.sh'),'https://stats.jun-liang-lyu.com',tag)
    pending=BASE/'current.new'
    if pending.is_symlink(): pending.unlink()
    pending.symlink_to(rel,target_is_directory=True)
    pending.replace(BASE/'current')


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--apply',action='store_true'); args=parser.parse_args()
    if args.apply and os.environ.get('STATS_GATEWAY_READY')!='1':
        raise ValueError('Shared gateway must be explicitly approved and ready before installation')
    request=Request(f'https://api.github.com/repos/{REPO}/releases/latest',headers={'User-Agent':'stats-release-puller'})
    with urlopen(request,timeout=30) as response: metadata=json.load(response)
    tag=metadata.get('tag_name','')
    if not re.fullmatch('release-'+ID_PATTERN,tag): raise ValueError('Not a stats release')
    if metadata.get('draft') or metadata.get('prerelease'): raise ValueError('Not a production release')
    if metadata.get('author',{}).get('login') not in ('github-actions[bot]','Junliang-Lyu'):
        raise ValueError('Unapproved publisher')
    rid=tag.removeprefix('release-'); name=f'stats-release-{rid}.tar.gz'
    assets={a['name']:a['browser_download_url'] for a in metadata.get('assets',[])}
    if name not in assets or name+'.sha256' not in assets: raise ValueError('Missing release assets')
    with tempfile.TemporaryDirectory(prefix='stats-release-') as directory:
        tmp=Path(directory); pack=tmp/name; digest=tmp/(name+'.sha256')
        fetch(assets[name],pack,3_000_000_000); fetch(assets[name+'.sha256'],digest,4096)
        expected=digest.read_text().split()[0]
        if not re.fullmatch('[a-fA-F0-9]{64}',expected): raise ValueError('Invalid checksum')
        with pack.open('rb') as f: actual=hashlib.file_digest(f,'sha256').hexdigest()
        if actual!=expected.lower(): raise ValueError('Checksum mismatch')
        validate_archive(pack,rid)
        print('Verified stats release:',tag)
        if not args.apply:
            print('Verification only; no server paths, containers or configuration changed.')
            return
        import fcntl
        state=BASE/'state'; releases=BASE/'releases'
        state.mkdir(parents=True,exist_ok=True); releases.mkdir(parents=True,exist_ok=True)
        with (state/'deploy.lock').open('w') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            good=state/'last_good'; bad=state/'last_failed'
            if any(p.exists() and p.read_text().strip()==tag for p in (good,bad)): return
            previous=good.read_text().strip() if good.exists() else None
            if previous and not re.fullmatch('release-'+ID_PATTERN,previous): raise ValueError('Invalid prior release')
            rel=releases/rid
            if rel.exists(): raise ValueError('Release directory exists; inspect before retrying')
            rel.mkdir(mode=0o755)
            # Only explicitly validated regular files; no extractall or archive links.
            with tarfile.open(pack,'r:gz') as archive:
                for member in archive.getmembers():
                    if member.isfile():
                        with archive.extractfile(member) as src, (rel/PurePosixPath(member.name).name).open('xb') as dst:
                            shutil.copyfileobj(src,dst)
            run('docker','load','-i',str(rel/f'stats-api-{rid}.tar'))
            run('docker','image','inspect',f'stats-api:{rid}','--format','{{.Id}}')
            try:
                switch(rel,tag)
            except Exception:
                bad.write_text(tag+'\n')
                if previous: switch(releases/previous.removeprefix('release-'),previous)
                else:
                    run('docker','compose','--project-name','stats','--env-file',str(state/'release.env'),'-f',str(rel/'compose.stats.yaml'),'stop','stats-api')
                raise RuntimeError('Stats release failed checks; rollback attempted. No other service was changed.') from None
            good.write_text(tag+'\n')
            print('Stats release passed:',tag)


if __name__=='__main__':
    try: main()
    except Exception:
        # Do not print command stderr, environment, request bodies or provider credentials.
        print('Stats release verification/deployment failed; existing services were not targeted.')
        raise SystemExit(1)
