"""Run a clean copy in a new standard-library-only Python environment."""
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import venv

root = Path(__file__).resolve().parent
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
workspace = root / '.local-history' / ('cold-run-' + stamp)
workspace.mkdir(parents=True)
names = ['project1.py','project1_model.py','test_project1.py','lab11_nvda.py',
         'nvda-20260125.html','requirements.txt','README.md']
log = ['Clean-environment run: '+stamp,
       'Fresh directory and venv; system site packages disabled; no pip dependencies.',
       'Runner: cold_run_project1.py',
       '\nSource SHA-256:']
for name in names:
    shutil.copy2(root/name,workspace/name)
    log.append(name+' '+hashlib.sha256((root/name).read_bytes()).hexdigest())
env_path = workspace/'venv'
venv.EnvBuilder(with_pip=False,system_site_packages=False).create(env_path)
python = env_path / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
environment = dict(os.environ)
environment.pop('PYTHONPATH',None)
environment.pop('PYTHONHOME',None)
environment['PYTHONIOENCODING'] = 'utf-8'
ok = True
for args in [['--version'],['-m','unittest','test_project1','-v'],['project1.py']]:
    result = subprocess.run([str(python),*args],cwd=workspace,env=environment,
                            capture_output=True,text=True,encoding='utf-8',timeout=120)
    log.extend(['\nCOMMAND: python '+' '.join(args),'EXIT: '+str(result.returncode),
                result.stdout,result.stderr])
    ok = ok and result.returncode == 0
log.append('OVERALL: '+('PASS' if ok else 'FAIL'))
(root/'outputs').mkdir(exist_ok=True)
(root/'outputs/project1-cold-run.txt').write_text('\n'.join(log),encoding='utf-8')
print('Cold run '+('PASS' if ok else 'FAIL')+'; see outputs/project1-cold-run.txt')
raise SystemExit(0 if ok else 1)
