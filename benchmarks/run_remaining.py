import json,time,urllib.request,random
random.seed(42)
def solve(n,t,to=120):
    try:
        r=urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8080/api/solve',data=json.dumps({'numbers':n,'target':str(t),'timeout':to}).encode(),headers={'Content-Type':'application/json'}),timeout=to+15)
        return json.loads(r.read())
    except: return {'result':'error','winner':'N/A','time_ns':0}
def gk(n,b,f):
    v=[random.randint(2**(b-1),2**b-1) for _ in range(n)]; k=max(2,int(n*f)); s=random.sample(range(n),k); return ','.join(str(x) for x in v),sum(v[i] for i in s)
def gs(n,m):
    v=[random.randint(1,m) for _ in range(n)]; k=random.randint(2,min(20,n)); s=sorted(random.sample(range(n),k)); return ','.join(str(x) for x in v),sum(v[i] for i in s)
def gu(n):
    v=[10**9+i for i in range(1,n+1)]; k=random.randint(2,n); s=sorted(random.sample(range(n),k)); return ','.join(str(x) for x in v),sum(v[i] for i in s)
tests=[
    ('Sparse n=100',gs(100,1000)),
    ('Sparse n=200',gs(200,1000)),
    ('Sparse n=500',gs(500,1000)),
    ('5570',('1,3,7,21,50,200,400,499,1000,1500,2000,5000,10000,25000',5570)),
    ('Pow2 sum',('1,2,4,8,16,32,64,128,256,512,1024,2048,4096,8192,16384,32768,65536,131072,262144,524288',1048575)),
    ('Fib 20',('1,2,3,5,8,13,21,34,55,89,144,233,377,610,987,1597,2584,4181,6765,10946',17710)),
    ('Unique n=30',gu(30)),
    ('Unique n=40',gu(40)),
    ('Unique n=50',gu(50)),
    ('Advers n=20',gk(20,40,0.15)),
    ('Half-sum 105',(','.join(str(i) for i in range(1,21)),105)),
    ('Large gap',(','.join(str(x) for x in [1,1000,2000,3000,5000,8000,13000,21000,34000,55000,89000,144000,233000,377000,610000,987000,1597000,2584000,4181000,6765000]),6765000+55000+1000)),
    ('BigInt 40 100b',gk(40,100,0.3)),
    ('BigInt 44 128b',gk(44,128,0.3)),
    ('BigInt 48 128b',gk(48,128,0.3)),
    ('BigInt 52 128b',gk(52,128,0.3)),
    ('BigInt 56 128b',gk(56,128,0.3)),
]
for name,data in tests:
    if isinstance(data,tuple): n,t=data
    else: n,t=data[0],data[1]
    t0=time.time(); r=solve(n,t,300); t1=time.time()
    nel=len(n.split(',')) if n else 0
    md=max((len(x) for x in n.split(',')),default=0)
    print(f"{name:25s} n={nel:3d} d={md:3d} | {r['result']:12s} | {r['winner']:25s} | {(t1-t0)*1000:.0f}ms")
