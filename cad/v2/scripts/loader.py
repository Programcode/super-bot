# loader.py: the body passed to fusion_mcp_execute. Fetches v2lib.py and a stage file from
# the VPS file bridge, runs CALL, and uploads the log (or traceback) as run-<TAG>.txt,
# because long runs outlive the MCP call's timeout.
import adsk.core, urllib.request, traceback, time
U = 'http://100.115.45.111:8766/'
JOBS = [('s2_level0.py', "main(('cliff',))")]
TAG = 'job'


def run(_context: str):
    out = []
    t0 = time.time()
    try:
        for stage, call in JOBS:
            g = {'__name__': 'sbv2'}
            exec(urllib.request.urlopen(U + 'v2lib.py', timeout=30).read().decode(), g)
            exec(urllib.request.urlopen(U + stage, timeout=30).read().decode(), g)
            exec(call, g)
            out.append('%s %s ok (%.0fs)\n%s' % (stage, call, time.time() - t0, '\n'.join(g['LOG'][-40:])))
        status = 'OK'
        doc = adsk.core.Application.get().activeDocument
        if doc.name.startswith('Super bot - v2') and not TAG.startswith('shot'):
            doc.save('auto-save after ' + TAG + ': ' + ', '.join(j[0] + ' ' + j[1] for j in JOBS))
            out.append('saved version %s' % (doc.dataFile.versionNumber if doc.dataFile else '?'))
    except Exception:
        out.append(traceback.format_exc())
        status = 'FAIL'
    msg = status + '\n' + '\n'.join(out)
    urllib.request.urlopen(urllib.request.Request(U + 'run-' + TAG + '.txt', data=msg.encode(), method='PUT'), timeout=30).read()
    print(msg)
