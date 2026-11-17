# view.py: set the viewport camera (for quick checks with the MCP screenshot), and
# save viewport images to the VPS bridge (deliverable shots).
import os, tempfile


def cam(eye, target, up=(0, 0, 1), fov=26, ortho=False):
    vp = app.activeViewport
    c = vp.camera
    c.isSmoothTransition = False
    c.cameraType = adsk.core.CameraTypes.OrthographicCameraType if ortho else adsk.core.CameraTypes.PerspectiveCameraType
    c.perspectiveAngle = math.radians(fov)
    vp.camera = c
    adsk.doEvents()
    c = vp.camera
    c.isSmoothTransition = False
    c.eye = P(*eye)
    c.target = P(*target)
    c.upVector = adsk.core.Vector3D.create(*up)
    vp.camera = c
    vp.refresh()
    adsk.doEvents()


def save(name, w=1600, h=1200):
    vp = app.activeViewport
    path = os.path.join(tempfile.gettempdir(), name + '.png')
    vp.saveAsImageFile(path, w, h)
    put(name + '.png', open(path, 'rb').read())


def vis(prefixes, on=True, only=False):
    """Show/hide top-level occurrences by component-name prefix. only=True hides all others."""
    for o in root.occurrences:
        hit = any(o.component.name.startswith(p) for p in prefixes)
        if only:
            o.isLightBulbOn = hit
        elif hit:
            o.isLightBulbOn = on


def snap(name, w=1100, h=850):
    """Quick-look image via the bridge. v2lib's guard has already checked the active document."""
    save('look-' + name, w, h)


def save_t(name, w=1600, h=1200):
    """Viewport image with a transparent background (no grid/background); composited on the VPS."""
    vp = app.activeViewport
    path = os.path.join(tempfile.gettempdir(), name + '.png')
    o = adsk.core.SaveImageFileOptions.create(path)
    o.width, o.height = w, h
    o.isAntiAliased = True
    o.isBackgroundTransparent = True
    vp.saveAsImageFileWithOptions(o)
    put(name + '.png', open(path, 'rb').read())
