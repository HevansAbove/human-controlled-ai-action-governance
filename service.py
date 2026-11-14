"""Separate, UID-protected *mock* action executor and governance daemon.

This is research/demo code, not a production sandbox, identity system or security product.
No real email, payments, public posts or destructive file operations.
"""
import argparse
import hashlib
import hmac
import json
import os
import socket
import struct
import time
from pathlib import Path
from wire import canonical, signature, MAX_MESSAGE


class GovernanceService:
    def __init__(self, state, mode='reviewer', log_path=None):
        assert mode in {'baseline', 'rules', 'reviewer'}
        self.state, self.mode, self.log_path = state, mode, log_path
        self.docs = {k: dict(v) for k, v in state['documents'].items()}
        self.registry = state['registry']
        self.allowed = set(state['recipients'])
        self.agent_uid = int(state['agent_uid'])
        self.operator_uid = int(state['operator_uid'])
        self.used_nonces = set()
        self.pending = {}
        self.approvals = {}
        self.committed = set()
        self.last_external = {}
        self.events = []
        self.hash_head = '0'*64
        self.outbox = []

    def record(self, event, **data):
        rec = {'index': len(self.events) + 1, 'event': event, **data,
               'previous_hash': self.hash_head}
        rec['hash'] = hashlib.sha256(canonical(rec)).hexdigest()
        self.hash_head = rec['hash']
        self.events.append(rec)
        if self.log_path:
            with open(self.log_path, 'ab') as log:
                log.write(canonical(rec) + b'\n')
                log.flush()
                os.fsync(log.fileno())
        return rec

    def verify_log(self):
        prev = '0'*64
        for event in self.events:
            core = {k:v for k,v in event.items() if k != 'hash'}
            if core['previous_hash'] != prev or hashlib.sha256(canonical(core)).hexdigest() != event['hash']:
                return False
            prev = event['hash']
        return prev == self.hash_head

    def respond(self, decision, reason, request_id=None, **extra):
        return {'decision': decision, 'reason': reason, 'request_id': request_id, **extra}

    def _auth(self, msg, peer_uid):
        if not isinstance(msg, dict) or set(msg) != {'caller','nonce','request','signature'}:
            return False, 'schema'
        caller, nonce = msg['caller'], msg['nonce']
        if not isinstance(caller,str) or not isinstance(nonce,str) or not (8 <= len(nonce) <= 128):
            return False, 'schema'
        if not isinstance(msg['request'],dict) or not isinstance(msg['signature'],str):
            return False, 'schema'
        reg = self.registry.get(caller)
        if not reg or peer_uid != reg['uid']:
            return False, 'caller_or_uid'
        body = {k:msg[k] for k in ('caller','nonce','request')}
        if not hmac.compare_digest(signature(reg['key'],body),msg['signature']):
            return False, 'bad_signature'
        stamp = (caller,nonce)
        if stamp in self.used_nonces:
            return False, 'replay'
        self.used_nonces.add(stamp)
        return True, 'authenticated'

    def _schema(self, request):
        if set(request) != {'op','args'} or not isinstance(request['op'],str) or not isinstance(request['args'],dict):
            return False
        shapes = {
            'read_document': {'document'},
            'send_document': {'document','recipient'},
            'delete_document': {'document'},
            'save_draft': {'document'},
            'commit_approved': {'request_id'},
        }
        fields = shapes.get(request['op'])
        return fields is not None and set(request['args']) == fields and all(
            isinstance(x,str) and 0 < len(x) <= 256 for x in request['args'].values())

    def _hard_policy(self, caller, op, args):
        docid = args.get('document')
        doc = self.docs.get(docid)
        if not doc:
            return 'BLOCK','unknown_document'
        if op == 'send_document':
            recipient = args['recipient']
            if '@' not in recipient:
                return 'BLOCK','invalid_recipient'
            if doc['level'] == 'restricted' and recipient not in self.allowed:
                return 'BLOCK','restricted_external_destination'
            if doc['level'] == 'restricted':
                return 'ASK','restricted_document_approval'
            if recipient not in self.allowed:
                return 'ASK','unverified_recipient'
            if doc['level'] == 'internal':
                return 'ASK','internal_document_approval'
            return 'ACT','public_known_recipient'
        if op == 'delete_document':
            return 'ASK','destructive_action'
        if op == 'save_draft':
            return ('ACT','draft_saved') if doc['level'] == 'public' else ('ASK','private_draft_approval')
        if op == 'read_document':
            return 'ACT','read_authorised'
        return 'BLOCK','unsupported'

    def _run(self, caller, op, args, request_id):
        if request_id in self.committed:
            return self.respond('BLOCK','already_executed',request_id)
        if op == 'read_document':
            doc = self.docs[args['document']]
            if doc['source'] == 'external':
                self.last_external[caller] = {
                    'document': args['document'],
                    'suspicious': 'COMMAND ' in doc['content'] or 'ignore previous instructions' in doc['content'].lower(),
                }
            result = {'content': doc['content'], 'source': doc['source']}
        elif op == 'send_document':
            record = {'caller': caller, **args, 'document_level':self.docs[args['document']]['level']}
            self.outbox.append(record)
            result = {'sent':record}
        elif op == 'delete_document':
            self.docs.pop(args['document'],None)
            result = {'deleted':args['document']}
        elif op == 'save_draft':
            result = {'saved':args['document']}
        else:
            return self.respond('BLOCK','unsupported',request_id)
        self.committed.add(request_id)
        self.record('executed', caller=caller, action=op, args=args, request_id=request_id)
        return self.respond('ACT','executed',request_id,result=result)

    def _action(self, caller, request):
        op, args = request['op'], request['args']
        request_id = hashlib.sha256(canonical({'caller':caller,'request':request})).hexdigest()
        if request_id in self.committed:
            self.record('denied',caller=caller,reason='already_executed',request_id=request_id)
            return self.respond('BLOCK','already_executed',request_id)
        if self.mode == 'baseline':
            self.record('evaluated',caller=caller,decision='ACT',reason='unguarded',request_id=request_id)
            return self._run(caller,op,args,request_id)
        if op not in self.registry[caller]['capabilities']:
            self.record('denied',caller=caller,reason='capability_denied',request_id=request_id)
            return self.respond('BLOCK','capability_denied',request_id)
        decision,reason = self._hard_policy(caller,op,args)
        if self.mode == 'reviewer' and decision == 'ACT' and op in {'send_document','save_draft'}:
            # Advisory, deterministic, server-observed context; NOT a trained mini-AI.
            context = self.last_external.get(caller)
            if context and context['suspicious']:
                decision,reason = 'WAIT','reviewer_recent_untrusted_instruction'
        self.record('evaluated',caller=caller,decision=decision,reason=reason,request_id=request_id)
        if decision == 'ACT':
            return self._run(caller,op,args,request_id)
        if decision == 'ASK':
            self.pending[request_id] = (caller,dict(request))
        return self.respond(decision,reason,request_id)

    def _commit(self, caller, rid):
        entry = self.pending.get(rid)
        if not entry or entry[0] != caller:
            return self.respond('BLOCK','no_matching_pending_request',rid)
        approval = self.approvals.get(rid)
        if not approval:
            return self.respond('ASK','approval_missing',rid)
        if approval['revoked']:
            return self.respond('BLOCK','approval_revoked',rid)
        if approval['used'] or rid in self.committed:
            return self.respond('BLOCK','approval_consumed',rid)
        if time.monotonic() > approval['deadline']:
            return self.respond('BLOCK','approval_expired',rid)
        _, req = entry
        if req['op'] not in self.registry[caller]['capabilities']:
            return self.respond('BLOCK','capability_denied',rid)
        dec,reason = self._hard_policy(caller,req['op'],req['args'])
        if dec == 'BLOCK':
            return self.respond('BLOCK',reason,rid)
        # One-thread server + one local mock effect: the check and effect are serialised.
        approval['used'] = True
        result = self._run(caller,req['op'],req['args'],rid)
        self.pending.pop(rid,None)
        self.record('approved_commit',caller=caller,request_id=rid)
        return result

    def _operator(self,msg, peer_uid):
        if peer_uid != self.operator_uid:
            self.record('operator_rejected', reason='operator_uid_denied')
            return self.respond('BLOCK','operator_uid_denied')
        op = msg.get('op')
        rid = msg.get('request_id')
        if op in {'approve','revoke'} and isinstance(rid,str) and rid in self.pending:
            if op == 'approve':
                ttl = msg.get('ttl',60)
                if not isinstance(ttl,(float,int)) or isinstance(ttl,bool) or not (0 < ttl <= 600):
                    return self.respond('BLOCK','invalid_ttl')
                self.approvals[rid] = {'deadline': time.monotonic()+ttl,'used':False,'revoked':False}
            else:
                if rid not in self.approvals:
                    return self.respond('BLOCK','no_approval')
                self.approvals[rid]['revoked'] = True
            self.record('human_'+op,request_id=rid)
            return self.respond('ACT','human_'+op,rid)
        if op == 'state':
            return {'decision':'ACT','reason':'operator_state','executions':sum(e['event']=='executed' for e in self.events),
                    'outbox':self.outbox,'events':self.events,'audit_valid':self.verify_log(),
                    'documents':sorted(self.docs)}
        if op == 'change_level':
            document,level = msg.get('document'),msg.get('level')
            if document not in self.docs or level not in {'public','internal','restricted'}:
                return self.respond('BLOCK','invalid_level_change')
            self.docs[document]['level']=level
            self.record('human_changed_classification',document=document,level=level)
            return self.respond('ACT','classification_updated')
        return self.respond('BLOCK','invalid_operator_request')

    def handle(self,msg,peer_uid):
        if not isinstance(msg,dict):
            return self.respond('BLOCK','invalid_message')
        if msg.get('channel') == 'operator':
            return self._operator(msg,peer_uid)
        okay,reason = self._auth(msg,peer_uid)
        if not okay:
            self.record('authentication_failed',reason=reason,peer_uid=peer_uid)
            return self.respond('BLOCK',reason)
        req = msg['request']
        if not self._schema(req):
            self.record('denied',caller=msg['caller'],reason='invalid_schema')
            return self.respond('BLOCK','invalid_schema')
        if req['op'] == 'commit_approved':
            return self._commit(msg['caller'],req['args']['request_id'])
        return self._action(msg['caller'],req)


def server_main():
    p = argparse.ArgumentParser()
    p.add_argument('--socket',required=True)
    p.add_argument('--state',required=True)
    p.add_argument('--mode',choices=['baseline','rules','reviewer'],required=True)
    a=p.parse_args()
    secret_dir=Path(a.state).parent
    with open(a.state,encoding='utf8') as stream:
        state=json.load(stream)
    gate=GovernanceService(state,a.mode,str(secret_dir/'audit.jsonl'))
    path = Path(a.socket)
    try: path.unlink()
    except FileNotFoundError: pass
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as server:
        server.bind(a.socket)
        os.chmod(a.socket,0o666)  # Authentication uses SO_PEERCRED + per-caller HMAC.
        server.listen(10)
        while True:
            conn,_=server.accept()
            with conn:
                conn.settimeout(4)
                if not hasattr(socket,'SO_PEERCRED'):
                    response=gate.respond('BLOCK','unsupported_platform_no_peercred')
                else:
                    pid,uid,gid=struct.unpack('3i',conn.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,12))
                    buf=b''
                    try:
                        while b'\n' not in buf:
                            part=conn.recv(4096)
                            if not part: break
                            buf += part
                            if len(buf) > MAX_MESSAGE:
                                raise ValueError('message_too_long')
                        message=json.loads(buf.split(b'\n',1)[0])
                        response=gate.handle(message,uid)
                    except (ValueError,IndexError,KeyError,TypeError,UnicodeDecodeError) as e:
                        gate.record('protocol_rejected',error=type(e).__name__)
                        response=gate.respond('BLOCK','invalid_protocol')
                try: conn.sendall(canonical(response)+b'\n')
                except (OSError, BrokenPipeError): pass

if __name__=='__main__':
    server_main()
