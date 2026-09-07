#!/usr/bin/env python3
"""Exercise the real SFTP adapter with controlled SSH states, no network."""
import ast
from pathlib import Path
import sys,tempfile
from types import SimpleNamespace
from unittest.mock import Mock,patch


def load_adapter():
    root=Path(__file__).resolve().parents[1]/'indi_allsky/filetransfer'
    env={}
    for name in ('exceptions.py','generic.py','paramiko_sftp.py'):
        tree=ast.parse((root/name).read_text())
        tree.body=[n for n in tree.body if not isinstance(n,ast.ImportFrom) or not n.level]
        exec(compile(tree,name,'exec'),env)
    return env


def run():
    env=load_adapter();Adapter=env['paramiko_sftp']
    class SSHError(Exception):pass
    class AuthError(SSHError):pass
    class KeyErrorSSH(SSHError):pass
    class ConnectError(OSError):pass
    class InvalidKey(Exception):pass
    class Reject:pass
    class Auto:pass
    client=Mock()
    paramiko=SimpleNamespace(SSHClient=lambda:client,RejectPolicy=Reject,AutoAddPolicy=Auto,
        hostkeys=SimpleNamespace(InvalidHostKey=InvalidKey),ssh_exception=SimpleNamespace(SSHException=SSHError,AuthenticationException=AuthError,BadHostKeyException=KeyErrorSSH,NoValidConnectionsError=ConnectError))
    args=dict(hostname='test.invalid',username='test',password='test-password')
    with patch.dict(sys.modules,{'paramiko':paramiko}):
        adapter=Adapter({});adapter.connect(**args)
        client.load_system_host_keys.assert_called_once_with()
        policy=client.set_missing_host_key_policy.call_args.args[0]
        try:policy.missing_host_key(client,'test.invalid',None)
        except env['CertificateValidationFailure']:pass
        else:raise AssertionError('Unknown key accepted')
        assert isinstance(policy,Reject)
        for error,expected in ((KeyErrorSSH(), 'CertificateValidationFailure'),(AuthError(),'AuthenticationFailure'),(ConnectError(),'ConnectionFailure'),(SSHError(),'ConnectionFailure'),(EOFError(),'ConnectionFailure'),(ConnectionResetError(),'ConnectionFailure')):
            client.connect.side_effect=error
            try:Adapter({}).connect(**args)
            except env[expected]:pass
            else:raise AssertionError(type(error))
        client.connect.side_effect=None
        client.open_sftp.side_effect=SSHError('subsystem failed')
        try:Adapter({}).connect(**args)
        except env['ConnectionFailure']:pass
        else:raise AssertionError('Subsystem failure escaped')
        client.open_sftp.side_effect=None
        client.load_system_host_keys.side_effect=InvalidKey('bad format')
        try:Adapter({}).connect(**args)
        except env['CertificateValidationFailure']:pass
        else:raise AssertionError('Malformed trust store accepted')
        client.load_system_host_keys.side_effect=None
        adapter=Adapter({});adapter.connect(**dict(args,cert_bypass=True))
        assert isinstance(client.set_missing_host_key_policy.call_args.args[0],Auto)
        channel=adapter.sftp;channel.close.side_effect=SSHError('closed remotely');client.close.reset_mock()
        adapter.close();client.close.assert_called_once_with();adapter.close();client.close.assert_called_once_with()
        with tempfile.TemporaryDirectory() as folder:
            local=Path(folder)/'source';local.write_bytes(b'test')
            for stage in ('mkdir','put'):
                adapter=Adapter({});adapter.sftp=Mock();getattr(adapter.sftp,stage).side_effect=SSHError('disconnected')
                try:adapter.put(local_file=local,remote_file='test/result')
                except env['TransferFailure']:pass
                else:raise AssertionError(stage)
    print('SFTP: trusted-host loading, unknown/mismatched/malformed keys, auth/transport/subsystem/transfer failures, explicit legacy bypass and resilient close: PASS')

if __name__=='__main__':run()
