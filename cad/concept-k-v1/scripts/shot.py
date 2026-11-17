# shot.py: viewport screenshots from fixed cameras, uploaded to the VPS receiver.
import os, tempfile, urllib.request

VIEWS = {
    # explicit perspective cameras (fit() proved unreliable through the MCP bridge)
    'front_k': ((0, 3400, 380), (0, 0, 360), (0, 0, 1)),
    'side_k': ((3400, 0, 380), (0, 0, 360), (0, 0, 1)),
    'top_k': ((0, 1, 3400), (0, 0, 0), (0, 1, 0)),
    'iso_k': ((1500, 1900, 1150), (0, 0, 330), (0, 0, 1)),
    'body_k': ((1000, 1250, 620), (0, 0, 90), (0, 0, 1)),
    'rear_k': ((-1300, -1650, 900), (0, 0, 250), (0, 0, 1)),
    'head_k': ((330, 600, 720), (0, 48, 655), (0, 0, 1)),
    # name: (eye, target, up) in mm
    'front': ((0, 2600, 330), (0, 0, 330), (0, 0, 1)),
    'side': ((2600, 0, 330), (0, 0, 330), (0, 0, 1)),
    'rear': ((0, -2600, 330), (0, 0, 330), (0, 0, 1)),
    'top': ((0, 0, 3000), (0, 0, 0), (0, 1, 0)),
    'iso': ((1300, 1700, 1100), (0, 0, 300), (0, 0, 1)),
    'iso_low': ((900, 1100, 420), (0, 0, 130), (0, 0, 1)),
    'iso_rear': ((-1200, -1500, 1000), (0, 0, 250), (0, 0, 1)),
}


def shot(name, view, w=1400, h=1100, ortho=False, fov=None, eye=None, target=None, up=None):
    vp = app.activeViewport
    e, t, u = VIEWS[view] if view else (eye, target, up)
    # 1) angle first: Fusion re-derives the eye distance when the angle changes
    cam = vp.camera
    cam.isSmoothTransition = False
    cam.cameraType = adsk.core.CameraTypes.OrthographicCameraType if ortho else adsk.core.CameraTypes.PerspectiveCameraType
    cam.perspectiveAngle = math.radians(fov or 26)
    vp.camera = cam
    adsk.doEvents()
    # 2) then place the eye
    cam = vp.camera
    cam.isSmoothTransition = False
    cam.eye = P(*e)
    cam.target = P(*t)
    cam.upVector = adsk.core.Vector3D.create(*u)
    vp.camera = cam
    vp.refresh()
    adsk.doEvents()
    path = os.path.join(tempfile.gettempdir(), name + '.png')
    vp.saveAsImageFile(path, w, h)
    data = open(path, 'rb').read()
    req = urllib.request.Request('http://100.115.45.111:8765/' + name + '.png', data=data, method='PUT')
    urllib.request.urlopen(req, timeout=60).read()
    log('shot', name, len(data))
