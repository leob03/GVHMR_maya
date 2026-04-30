"""
Install GVHMR Maya as a Maya module and create a shelf button.

Run once in Maya's Python Script Editor:

    import runpy
    runpy.run_path("/path/to/GVHMR_maya/install_maya.py")
"""

import os
import sys

import maya.cmds as cmds
import maya.mel as mel


MODULE_NAME = "GVHMR_maya"
MODULE_VERSION = "1.0"
SHELF_NAME = "GVHMR"
SHELF_BUTTON_ANNOTATION = "Open GVHMR Maya Importer"


def _repo_dir():
    if "__file__" in globals():
        return os.path.dirname(os.path.abspath(__file__))

    selection = cmds.fileDialog2(fileMode=3, caption="Select GVHMR_maya Repository Folder")
    if not selection:
        raise RuntimeError("No GVHMR_maya repository folder selected.")
    return os.path.abspath(selection[0])


def _maya_app_dir():
    maya_app_dir = os.environ.get("MAYA_APP_DIR")
    if maya_app_dir:
        return os.path.abspath(os.path.expanduser(maya_app_dir))

    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Preferences/Autodesk/maya")
    return os.path.expanduser("~/maya")


def _write_module_file(repo_dir):
    modules_dir = os.path.join(_maya_app_dir(), "modules")
    if not os.path.isdir(modules_dir):
        os.makedirs(modules_dir)

    module_file = os.path.join(modules_dir, f"{MODULE_NAME}.mod")
    module_text = (
        f"+ {MODULE_NAME} {MODULE_VERSION} {repo_dir}\n"
        "PYTHONPATH +:= .\n"
    )
    with open(module_file, "w", encoding="utf-8") as f:
        f.write(module_text)
    return module_file


def _shelf_top_level():
    return mel.eval("$tmp = $gShelfTopLevel")


def _ensure_shelf():
    top_level = _shelf_top_level()
    shelves = cmds.tabLayout(top_level, query=True, childArray=True) or []
    if SHELF_NAME not in shelves:
        cmds.shelfLayout(SHELF_NAME, parent=top_level)
    return SHELF_NAME


def _remove_existing_button(shelf):
    buttons = cmds.shelfLayout(shelf, query=True, childArray=True) or []
    for button in buttons:
        try:
            annotation = cmds.shelfButton(button, query=True, annotation=True)
        except Exception:
            continue
        if annotation == SHELF_BUTTON_ANNOTATION:
            cmds.deleteUI(button)


def _create_shelf_button(repo_dir):
    if repo_dir not in sys.path:
        sys.path.append(repo_dir)

    shelf = _ensure_shelf()
    _remove_existing_button(shelf)

    command = (
        "import importlib\n"
        "import gvhmr_maya_importer\n"
        "importlib.reload(gvhmr_maya_importer)\n"
        "gvhmr_maya_importer.show()\n"
    )

    cmds.shelfButton(
        parent=shelf,
        label="GVHMR",
        annotation=SHELF_BUTTON_ANNOTATION,
        image1="commandButton.png",
        sourceType="python",
        command=command,
    )


def install():
    repo_dir = _repo_dir()
    if not os.path.isfile(os.path.join(repo_dir, "gvhmr_maya_importer.py")):
        raise RuntimeError(f"gvhmr_maya_importer.py not found in: {repo_dir}")

    module_file = _write_module_file(repo_dir)
    _create_shelf_button(repo_dir)

    message = (
        "GVHMR Maya installed.\n\n"
        f"Module file:\n{module_file}\n\n"
        "A GVHMR shelf button was created. Restart Maya later if you want the module file "
        "to be picked up from a completely fresh session."
    )
    cmds.confirmDialog(title="GVHMR Maya", message=message, button=["OK"])
    print(message)
    return module_file


if __name__ in ("__main__", "<run_path>"):
    install()
