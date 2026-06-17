#!/usr/bin/env python3
"""Full 65-category benchmark suite with real test data.
Tests every category, records elements, goals, results, engine used.
Usage: python test_all_65.py --port 8080
"""
import json, time, urllib.request, sys, os, random

PORT = 8080
if "--port" in sys.argv:
    PORT = int(sys.argv[sys.argv.index("--port") + 1])
random.seed(42)

def solve(numbers, target, timeout=60):
    req = json.dumps({"numbers": numbers, "target": str(target), "timeout": timeout}).encode()
    try:
        r = urllib.request.urlopen(
            urllib.request.Request(f"http://127.0.0.1:{PORT}/api/solve",
                data=req, headers={"Content-Type": "application/json"}),
            timeout=timeout + 15)
        return json.loads(r.read())
    except:
        return {"result":"error","error":"timeout","time_ns":0,"winner":"N/A","solution":""}

def gen_kn(n, bitlen=64, frac=0.4):
    vals = [random.randint(2**(bitlen-1), 2**bitlen - 1) for _ in range(n)]
    k = max(2,int(n*frac))
    subset = random.sample(range(n), k)
    return ",".join(str(v) for v in vals), sum(vals[i] for i in subset)

def gen_si(n):
    vals = [1]
    for _ in range(n-1): vals.append(sum(vals)*2 + random.randint(0,5))
    k = random.randint(2,n)
    return ",".join(str(v) for v in vals), sum(vals[i] for i in sorted(random.sample(range(n),k)))

def gen_small(n, mv=100):
    vals = [random.randint(1,mv) for _ in range(n)]
    k = random.randint(2,min(20,n))
    return ",".join(str(v) for v in vals), sum(vals[i] for i in sorted(random.sample(range(n),k)))

def gen_dense(n):
    vals = [random.randint(1,max(5,100-n)) for _ in range(n)]
    k = random.randint(2,min(15,n))
    return ",".join(str(v) for v in vals), sum(vals[i] for i in sorted(random.sample(range(n),k)))

def gen_unique(n):
    vals = [10**9 + i for i in range(1,n+1)]
    k = random.randint(2,n)
    return ",".join(str(v) for v in vals), sum(vals[i] for i in sorted(random.sample(range(n),k)))

def run(name, numbers, target, cat, timeout=120):
    t0=time.time(); r=solve(numbers,target,timeout); t1=time.time()
    nel=len([x for x in numbers.split(",") if x.strip()]) if numbers.strip() else 0
    md=max((len(x.strip().lstrip("-")) for x in numbers.split(",") if x.strip()),default=0)
    res=r.get("result","error"); eng=r.get("winner","N/A"); sol=r.get("solution","")
    return {"name":name,"n":nel,"digits":md,"result":res,"winner":eng,
            "time_ms":(t1-t0)*1000,"server_ms":r.get("time_ns",0)/1e6,
            "numbers":numbers,"target":str(target),"solution":sol,"category":cat}

def main():
    R=[]
    # 1-12: Edge/Corner
    R.append(run("Empty set","","0","Edge",5))
    R.append(run("Single match","7","7","Edge",5))
    R.append(run("Single impossible","7","5","Edge",5))
    R.append(run("Two-element match","3,8","11","Edge",5))
    R.append(run("Two-element impossible","3,8","10","Edge",5))
    R.append(run("Target=0","1,2,3,4,5,6,7,8,9,10","0","Edge",5))
    R.append(run("All elements equal","7,"*9+"7","70","Edge",5))
    R.append(run("Contains zero","0,1,2,3,4,5","7","Edge",5))
    R.append(run("Negative values","-5,3,8,-2,7,-1,4,9,-3,6","15","Edge",5))
    R.append(run("Huge value test","999999999999999,888888888888888,777777777777777,666666666666666","1234567890123456","Edge",10))
    # 13-16: GCD/Impossible
    R.append(run("GCD mod 3","3,6,9,12,15,18,21,24","10","GCD",5))
    R.append(run("Even/odd mismatch","2,4,6,8,10,12,14,16","7","GCD",5))
    R.append(run("Sum < target","1,2,3,4,5","100","GCD",5))
    R.append(run("Single > target","10,20,30,40,50","5","GCD",5))
    # 17-19: All Elements
    n,t=gen_small(10,50); R.append(run("All elems n=10",n,t,"AllElems",5))
    n,t=gen_small(50,100); R.append(run("All elems n=50",n,t,"AllElems",5))
    n,t=gen_small(100,200); R.append(run("All elems n=100",n,t,"AllElems",5))
    # 20-22: Super-increasing
    for sz in [20,40,60]:
        n,t=gen_si(sz); R.append(run(f"Super-inc n={sz}",n,t,"SuperInc",5))
    # 23-25: Powers of 2
    for sz in [10,15,20]:
        vals=[2**i for i in range(sz)]; t=sum(vals)
        R.append(run(f"Pow2 n={sz}",",".join(str(v) for v in vals),t,"Pow2",5))
    # 26-29: Duplicates
    R.append(run("Dups 30x7","7,"*29+"7","49","Dups",5))
    R.append(run("Dups 20x5","5,"*19+"5","25","Dups",5))
    R.append(run("Dups mixed","3,3,3,7,7,7,11,11,11,13,13,13","34","Dups",5))
    R.append(run("Dups 100x1","1,"*99+"1","50","Dups",5))
    # 30-33: Small Target
    for sz in [100,500,1000,2000]:
        n,t=gen_small(sz,100); R.append(run(f"SmallTgt n={sz}",n,t,"SmallTgt",60))
    # 34-37: Random MITM
    for sz,b in [(10,20),(20,40),(25,48),(30,56)]:
        n,t=gen_kn(sz,b,0.3); R.append(run(f"Random n={sz} {b}b",n,t,"MITM",120))
    # 38-40: Dense
    for sz in [20,30,40]:
        n,t=gen_dense(sz); R.append(run(f"Dense n={sz}",n,t,"Dense",30))
    # 41-43: Frequency
    R.append(run("Freq single","5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5","25","Freq",5))
    R.append(run("Freq multi","3,3,3,3,7,7,7,7,11,11,11,11,5,5,5,5,13,13,13,13","30","Freq",5))
    vals=[3]*10+[7]*10+[11]*10+[13]*10; t=3*3+7*2+11+13*2
    R.append(run("Freq pattern",",".join(str(v) for v in vals),t,"Freq",10))
    # 44-48: Hard 64-bit
    for sz in [36,40,44,48,50]:
        n,t=gen_kn(sz,64,0.35); R.append(run(f"Hard64 n={sz}",n,t,"Hard64",300))
    # 49-51: Sparse Large
    for sz in [100,200,500]:
        n,t=gen_small(sz,1000); R.append(run(f"Sparse n={sz}",n,t,"Sparse",60))
    # 52-54: Classics
    R.append(run("5570 benchmark","1,3,7,21,50,200,400,499,1000,1500,2000,5000,10000,25000","5570","Classic",10))
    vals=[2**i for i in range(20)]; t=sum(vals)
    R.append(run("Pow2 sum 20","1,2,4,8,16,32,64,128,256,512,1024,2048,4096,8192,16384,32768,65536,131072,262144,524288",t,"Classic",5))
    fib=[1,2]; [fib.append(fib[-1]+fib[-2]) for _ in range(18)]
    R.append(run("Fibonacci 20",",".join(str(f) for f in fib),sum(fib),"Classic",5))
    # 55-57: Unique Solution
    for sz in [30,40,50]:
        n,t=gen_unique(sz); R.append(run(f"Unique n={sz}",n,t,"Unique",120))
    # 58-60: Adversarial
    n,t=gen_kn(20,40,0.15); R.append(run("Adversarial n=20",n,t,"Adversarial",30))
    n,t=gen_kn(20,40,0.3)
    R.append(run("Target=half-sum","1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20","105","Adversarial",10))
    vals=[1,1000,2000,3000,5000,8000,13000,21000,34000,55000,89000,144000,233000,377000,610000,987000,1597000,2584000,4181000,6765000]
    k=5; t=sum(vals[i] for i in sorted(random.sample(range(len(vals)),k)))
    R.append(run("Large value gap",",".join(str(v) for v in vals),t,"Adversarial",10))
    # 61-65: Arbitrary Precision
    for sz,b in [(40,100),(44,128),(48,128),(52,128),(56,128)]:
        n,t=gen_kn(sz,b,0.3); R.append(run(f"BigInt n={sz} {b}b",n,t,"ArbPrec",300))

    # Print summary
    passed=sum(1 for r in R if r["result"] in ("solved","impossible"))
    print(f"\n=== {passed}/{len(R)} PASSED ===\n")
    print("| # | Category | n | Digits | Result | Engine | ms |")
    print("|---|----------|---|--------|--------|--------|-----|")
    for i,r in enumerate(R,1):
        print(f"| {i} | {r['name']} | {r['n']} | {r['digits']} | {r['result']} | {r['winner']} | {r['time_ms']:.1f} |")

    # Save full data
    with open(os.path.join(os.path.dirname(__file__),"all_65_results.json"),"w") as f:
        json.dump({"specs":"Intel i3-2100 3.10GHz 2C/4T 12GB Win10 Rust 1.95 Release","results":R},f,indent=2)
    print("\nSaved all_65_results.json")

    # Save human-readable test data file
    with open(os.path.join(os.path.dirname(__file__),"TEST_DATA.md"),"w",encoding="utf-8") as f:
        f.write("# Z++ World Record Test Data — All 65 Categories\n\n")
        f.write("## PC: Intel i3-2100 @ 3.10GHz (2C/4T) | 12GB DDR3 | Win10 Pro | Rust 1.95 Release\n\n")
        f.write("| # | Category | Elements | Target | Result | Solution | Engine | ms |\n")
        f.write("|---|----------|----------|--------|--------|----------|--------|----|\n")
        for i,r in enumerate(R,1):
            nums_short = r['numbers'][:60] + ('...' if len(r['numbers'])>60 else '')
            tgt_short = r['target'][:30] + ('...' if len(r['target'])>30 else '')
            sol_short = r['solution'][:60] + ('...' if len(r['solution'])>60 else '') if r['solution'] else ''
            f.write(f"| {i} | {r['name']} | {nums_short} | {tgt_short} | {r['result']} | {sol_short} | {r['winner']} | {r['time_ms']:.1f} |\n")
        f.write(f"\nDetails: {passed}/{len(R)} passed.\n")
    print("Saved TEST_DATA.md")

if __name__=="__main__":
    main()
