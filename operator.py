"""Demonstration operator tool: server authenticates kernel UID, not text labels."""
import argparse, json
from wire import exchange

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--socket',required=True)
    parser.add_argument('op',choices=['state','approve','revoke','change_level'])
    parser.add_argument('--request-id',default='')
    parser.add_argument('--document',default='')
    parser.add_argument('--level',default='')
    parser.add_argument('--ttl',type=float,default=60)
    args=parser.parse_args()
    print(json.dumps(exchange(args.socket,{'channel':'operator','op':args.op,
                                          'request_id':args.request_id,'document':args.document,
                                          'level':args.level,'ttl':args.ttl})))
