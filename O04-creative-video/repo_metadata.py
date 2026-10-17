#!/usr/bin/env python3
import hashlib, json, pathlib, subprocess
root = pathlib.Path(__file__).resolve().parent
repos = {
    'ffmpeg': ['LICENSE.md', 'COPYING.LGPLv2.1', 'COPYING.GPLv2'],
    'opentimelineio': ['LICENSE.txt'],
    'c2pa-rs': ['LICENSE-APACHE', 'LICENSE-MIT', 'cli/Cargo.toml'],
    'vbench': ['LICENSE', 'requirements.txt'],
    'videoscore': ['LICENSE'],
    'twelvelabs-python': ['0.4/LICENSE', 'pyproject.toml'],
    'hume-python-sdk': ['LICENSE', 'pyproject.toml'],
    'opentelemetry-specification': ['LICENSE'],
    'whisper': ['LICENSE', 'pyproject.toml'],
}
def git(path, *args):
    return subprocess.check_output(['git', '-C', str(path), *args], text=True).strip()
def tree_bytes(path):
    return sum(p.stat().st_size for p in path.rglob('*') if p.is_file())
out=[]
for name, license_paths in repos.items():
    p=root/'repos'/name
    archive=subprocess.check_output(['git','-C',str(p),'archive','--format=tar','HEAD'])
    lic=[]
    for rel in license_paths:
        lp=p/rel
        lic.append({'path':rel,'exists':lp.exists(),'sha256':hashlib.sha256(lp.read_bytes()).hexdigest() if lp.exists() else ''})
    out.append({
        'candidate':name,
        'origin':git(p,'remote','get-url','origin'),
        'commit':git(p,'rev-parse','HEAD'),
        'tree':git(p,'rev-parse','HEAD^{tree}'),
        'describe':git(p,'describe','--tags','--always'),
        'commit_date':git(p,'show','-s','--format=%cI','HEAD'),
        'archive_sha256':hashlib.sha256(archive).hexdigest(),
        'working_tree_bytes':tree_bytes(p),
        'license_files':lic,
    })
text=json.dumps(out,indent=2)
(root/'repo-metadata.json').write_text(text+'\n')
print(text)
