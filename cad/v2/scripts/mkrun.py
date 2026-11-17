# prints the loader with JOBS/TAG substituted, as a JSON string for the MCP call
import sys, json, re
src = open('cad/v2/scripts/loader.py').read()
tag = sys.argv[1]; jobs = sys.argv[2]
src = re.sub(r"^JOBS = .*$", "JOBS = " + jobs, src, flags=re.M)
src = re.sub(r"^TAG = .*$", "TAG = %r" % tag, src, flags=re.M)
print(src)
