"""
py2app build script for Mini Process Viewer.

Usage:
    python3 setup.py py2app
"""

import glob
import os
import shutil
from setuptools import setup
from setuptools.command.build_py import build_py

_BUILD_DIR = os.path.expanduser("~/caffeinate-ui-build")

# Clean previous build to avoid stale files
for _d in ("build", "dist"):
    _path = os.path.join(_BUILD_DIR, _d)
    if os.path.isdir(_path):
        shutil.rmtree(_path, ignore_errors=True)

# Frameworks the app actually needs (QtWidgets depends on QtPrintSupport,
# QtDBus is needed by the cocoa platform plugin).
_KEEP_FRAMEWORKS = {
    "QtCore.framework", "QtGui.framework", "QtWidgets.framework",
    "QtPrintSupport.framework", "QtDBus.framework", "QtMacExtras.framework",
}
# Qt plugins the app actually needs
_KEEP_PLUGINS = {"platforms", "styles"}
# Qt dirs to remove entirely
_REMOVE_DIRS = {"qml", "translations", "qsci"}

APP = ["caffeinate_qtUI.py"]
OPTIONS = {
    "argv_emulation": False,
    "iconfile": "AppIcon.icns",
    "bdist_base": os.path.join(_BUILD_DIR, "build"),
    "dist_dir": os.path.join(_BUILD_DIR, "dist"),
    "plist": {
        "CFBundleName": "Mini Process Viewer",
        "CFBundleDisplayName": "Mini Process Viewer",
        "CFBundleIdentifier": "com.local.miniprocessviewer",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0",
        "LSMinimumSystemVersion": "11.0",
        "NSHighResolutionCapable": True,
        "NSRequiresAquaSystemAppearance": False,
    },
    "includes": [
        "PyQt5.QtCore",
        "PyQt5.QtGui",
        "PyQt5.QtWidgets",
        "PyQt5.sip",
    ],
    "excludes": [
        "PyQt5.QtWebEngine", "PyQt5.QtWebEngineCore", "PyQt5.QtWebEngineWidgets",
        "PyQt5.QtWebChannel", "PyQt5.QtWebSockets",
        "PyQt5.QtMultimedia", "PyQt5.QtMultimediaWidgets",
        "PyQt5.QtNetwork", "PyQt5.QtNetworkAuth",
        "PyQt5.QtBluetooth", "PyQt5.QtNfc",
        "PyQt5.QtLocation", "PyQt5.QtPositioning",
        "PyQt5.QtQuick", "PyQt5.QtQuickWidgets", "PyQt5.QtQml",
        "PyQt5.QtQuick3D",
        "PyQt5.QtDesigner", "PyQt5.QtHelp", "PyQt5.QtTest",
        "PyQt5.QtOpenGL", "PyQt5.QtSvg", "PyQt5.QtXml",
        "PyQt5.QtSql", "PyQt5.QtDBus",
        "PyQt5.QtSensors", "PyQt5.QtSerialPort",
        "PyQt5.QtRemoteObjects", "PyQt5.QtTextToSpeech",
        "PyQt5.Qsci",
        "tkinter", "unittest", "pydoc", "doctest", "test",
    ],
    "qt_plugins": ["platforms/libqcocoa*", "styles/libqmacstyle*"],
}


def _trim_bundle():
    """Remove unused Qt5 frameworks, plugins, and dirs from the built .app."""
    app_dir = os.path.join(_BUILD_DIR, "dist", "Mini Process Viewer.app")
    qt5 = os.path.join(
        app_dir, "Contents", "Resources", "lib", "python3.9", "PyQt5", "Qt5",
    )
    # Remove unneeded frameworks
    lib_dir = os.path.join(qt5, "lib")
    if os.path.isdir(lib_dir):
        for name in os.listdir(lib_dir):
            if name.endswith(".framework") and name not in _KEEP_FRAMEWORKS:
                shutil.rmtree(os.path.join(lib_dir, name))
    # Remove unneeded plugin dirs
    plugins_dir = os.path.join(qt5, "plugins")
    if os.path.isdir(plugins_dir):
        for name in os.listdir(plugins_dir):
            if name not in _KEEP_PLUGINS:
                path = os.path.join(plugins_dir, name)
                if os.path.isdir(path):
                    shutil.rmtree(path)
    # Remove qml, translations, qsci dirs
    for name in _REMOVE_DIRS:
        path = os.path.join(qt5, name)
        if os.path.isdir(path):
            shutil.rmtree(path)
    # Remove unused .so bindings
    bindings = os.path.join(
        app_dir, "Contents", "Resources", "lib", "python3.9", "PyQt5",
    )
    keep_so = {"QtCore", "QtGui", "QtWidgets", "sip"}
    for f in glob.glob(os.path.join(bindings, "*.so")):
        base = os.path.basename(f).split(".")[0]
        if base not in keep_so:
            os.remove(f)
    # Remove uic (designer helper)
    uic = os.path.join(bindings, "uic")
    if os.path.isdir(uic):
        shutil.rmtree(uic)


setup(
    app=APP,
    name="Mini Process Viewer",
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)

# Run trim after setup() completes
if "py2app" in os.sys.argv:
    _trim_bundle()
    app_path = os.path.join(_BUILD_DIR, "dist", "Mini Process Viewer.app")
    print(f"\n✅ Built: {app_path}")
    total = sum(
        os.path.getsize(os.path.join(dp, f))
        for dp, _, fns in os.walk(app_path) for f in fns
    )
    print(f"   Size: {total / 1024 / 1024:.1f} MB")
