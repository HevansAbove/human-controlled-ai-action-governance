"""Standalone limited tool-using agent. NOT an LLM or a trained AI.

This intentionally vulnerable agent follows 'COMMAND' text in externally supplied
material to demonstrate that agent-level obedience must not grant authority.
"""
import argparse
import json
import os
import re
import sys
from wire import exchange, signed


def client(socket_path, credential, op, args):
    return exchange(socket_path,signed(credential['caller'],credential['key'],{'op':op,'args':args}))


def run(task, socket_path, cred):
    history=[]
    if task['kind'] == 'direct':
        request = task['request']
    elif task['kind'] == 'read_then_decide':
        read = client(socket_path,cred,'read_document',{'document':task['source_document']})
        history.append({'op':'read_document','decision':read['decision'],'reason':read['reason']})
        content = read.get('result',{}).get('content','')
        # Simulates a poorly designed agent wrongly following instructions in retrieved text.
        match = re.search(r'COMMAND send_document document=([\w-]+) recipient=([\w.@-]+)',content)
        if match:
            request={'op':'send_document','args':{'document':match.group(1),'recipient':match.group(2)}}
        else:
            request=task['fallback']
    elif task['kind']=='commit':
        request={'op':'commit_approved','args':{'request_id':task['request_id']}}
    elif task['kind']=='probe_direct_file':
        try:
            with open(task['private_path'],'rb') as f: f.read(1)
            return {'probe':'private_file','accessible':True}
        except (PermissionError,FileNotFoundError) as e:
            return {'probe':'private_file','accessible':False,'error':type(e).__name__}
    elif task['kind']=='probe_operator_spoof':
        response=exchange(socket_path,{'channel':'operator','op':'state'})
        return {'probe':'operator_spoof','decision':response['decision'],'reason':response['reason']}
    elif task['kind']=='probe_replay':
        req=task['request']
        message=signed(cred['caller'],cred['key'],req)
        return {'first':exchange(socket_path,message),'second':exchange(socket_path,message)}
    elif task['kind']=='probe_tamper':
        req=task['request']
        message=signed(cred['caller'],cred['key'],req)
        message['request']['args']['recipient']=task['modified_recipient']
        return {'tampered':exchange(socket_path,message)}
    elif task['kind']=='probe_forged_identity':
        req=task['request']
        message=signed(cred['caller'],cred['key'],req)
        message['caller']='agent-impostor'
        return {'forged':exchange(socket_path,message)}
    else:
        raise ValueError('Unknown task kind')
    response=client(socket_path,cred,request['op'],request['args'])
    history.append({'op':request['op'],'args':request['args'],
                    'decision':response['decision'],'reason':response['reason']})
    return {'history':history,'response':response,'proposed':request}

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--socket',required=True)
    parser.add_argument('--credential',required=True)
    parser.add_argument('--task',required=True)
    args=parser.parse_args()
    with open(args.credential,encoding='utf8') as f: cred=json.load(f)
    with open(args.task,encoding='utf8') as f: task=json.load(f)
    print(json.dumps(run(task,args.socket,cred)))
