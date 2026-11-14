"""End-to-end example of ASK > human approval > agent commit and revocation."""
import json
from harness import Sandbox, DIRECT, FOLLOW


def main():
    with Sandbox('reviewer') as s:
        steps=[]
        good=s.agent(DIRECT('send_document',document='weekly_report',recipient='colleague@lab.test'))
        steps.append({'step':'routine legitimate','decision':good['response']['decision']})
        req=s.agent(DIRECT('send_document',document='weekly_report',recipient='newfriend@elsewhere.test'))
        rid=req['response']['request_id']
        steps.append({'step':'new recipient requires review','decision':req['response']['decision']})
        steps.append({'step':'human approval','decision':s.operator('approve',request_id=rid)['decision']})
        commit=s.agent({'kind':'commit','request_id':rid})
        steps.append({'step':'agent executes approved exact action','decision':commit['response']['decision']})
        deletion=s.agent(DIRECT('delete_document',document='internal_plan'))
        rid=deletion['response']['request_id']
        s.operator('approve',request_id=rid)
        s.operator('revoke',request_id=rid)
        attempted=s.agent({'kind':'commit','request_id':rid})
        steps.append({'step':'human revokes deletion','decision':attempted['response']['decision'],
                      'reason':attempted['response']['reason']})
        injected=s.agent(FOLLOW('external_launder'))
        steps.append({'step':'untrusted instruction in document','decision':injected['response']['decision'],
                      'reason':injected['response']['reason']})
        state=s.operator('state')
        print(json.dumps({'steps':steps,'mock_sent_documents':state['outbox'],
                          'remaining_docs':state['documents'], 'audit_valid':state['audit_valid']},indent=2))

if __name__=='__main__':
    main()
