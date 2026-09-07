#!/usr/bin/env python3
"""Real SFTP over loopback to disposable files, with the installed host key pinned.

Run on the Raspberry as its normal user. Password is prompted without echo and
never saved. No production destination, media or known_hosts file is modified.
"""
import argparse,base64,getpass,hashlib,json,sys,tempfile
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def run(output):
    import paramiko
    from indi_allsky.filetransfer.paramiko_sftp import paramiko_sftp
    from indi_allsky.filetransfer.exceptions import TransferFailure
    parts=Path('/etc/ssh/ssh_host_ed25519_key.pub').read_text().split()
    key=paramiko.Ed25519Key(data=base64.b64decode(parts[1]))
    actual_client=paramiko.SSHClient
    def trusted_client():
        client=actual_client()
        client.get_host_keys().add('127.0.0.1',key.get_name(),key)
        return client
    password=getpass.getpass('Password for the current Raspberry user (loopback SFTP only): ')
    report={'observed_at':datetime.now(timezone.utc).isoformat(),'scope':'Real SSH/SFTP loopback; temporary source/destination only; not an external integration acceptance',
            'host_key_verified':True,'cert_bypass':False,'checks':[]}
    with tempfile.TemporaryDirectory(prefix='hybrid-sftp-acceptance-') as folder:
        root=Path(folder);source=root/'source.json';remote=root/'remote'/'camera-2'/'data.json'
        source.write_text(json.dumps({'camera_id':2,'profile_id':'test-profile-2','purpose':'disposable acceptance'},sort_keys=True))
        adapter=paramiko_sftp({});adapter.timeout=10
        denied=root/'denied';denied.mkdir();denied.chmod(0o500)
        try:
            with patch('paramiko.SSHClient',side_effect=trusted_client):
                adapter.connect(hostname='127.0.0.1',username=getpass.getuser(),password=password,cert_bypass=False)
            adapter.put(local_file=source,remote_file=remote)
            assert remote.is_file() and remote.read_bytes()==source.read_bytes()
            report['checks'].append({'case':'nested destination transfer','status':'superato','bytes':remote.stat().st_size,'sha256':hashlib.sha256(remote.read_bytes()).hexdigest()})
            try:adapter.put(local_file=source,remote_file=denied/'blocked.json')
            except TransferFailure:pass
            else:raise AssertionError('Write-denied destination unexpectedly accepted upload')
            assert not (denied/'blocked.json').exists() and source.is_file()
            report['checks'].append({'case':'permission failure preserves source','status':'superato'})
        finally:
            password=None
            adapter.close();denied.chmod(0o700)
        assert adapter.client is None and adapter.sftp is None
    assert not root.exists()
    report['checks'].append({'case':'connection close and disposable-directory cleanup','status':'superato'})
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    run(parser.parse_args().output)
