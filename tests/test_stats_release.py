import io
import tarfile
import pytest
from deploy.server.auto_deploy import validate_archive


def test_release_validation_rejects_traversal_symlinks_and_missing_files(tmp_path):
    rid='20261012T120000Z'
    for name,kind in [(rid+'/../bad','file'),(rid+'/stats.caddy','link'),(rid+'/release.txt','file')]:
        path=tmp_path/(kind+name.split('/')[-1]+'.tar.gz')
        with tarfile.open(path,'w:gz') as a:
            member=tarfile.TarInfo(name)
            if kind=='link': member.type=tarfile.SYMTYPE; member.linkname='/etc/passwd'; a.addfile(member)
            else: member.size=1; a.addfile(member,io.BytesIO(b'x'))
        with pytest.raises(ValueError): validate_archive(path,rid)


def test_complete_release_validates(tmp_path):
    rid='20261012T120000Z'; path=tmp_path/'release.tar.gz'
    with tarfile.open(path,'w:gz') as a:
        for name in ('compose.stats.yaml','stats.caddy','check-release.sh','release.txt',f'stats-api-{rid}.tar'):
            m=tarfile.TarInfo(rid+'/'+name); m.size=1; a.addfile(m,io.BytesIO(b'x'))
    validate_archive(path,rid)
