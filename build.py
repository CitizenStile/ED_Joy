import sys

import PyInstaller.__main__
import questionary as quest

"""Scripts to allow poetry to build using PyInstaller
"""

"""BEGIN - Common functions for build specs"""
additional_files = [
    ('assets', 'assets'),
    ('config', 'config'),
    ('pyproject.toml', '.'),
]

icon = ['assets\\icon.ico']
entry = ['main.py']
name = 'ed_joy'

"""END - Common functions for build specs  """
"""
Only the following command-line options have an effect when building from a spec file:
    --upx-dir
    --distpath
    --workpath
    --noconfirm
    --clean
    --log-level
"""

def file():
    # print("Building file")
    call_installer("ed_joy_onefile.spec","dist\\onefile")

def folder():
    call_installer("ed_joy_folder.spec","dist\\folder")

def both():
    folder()
    file()

def call_installer(spec, dist_path):
    PyInstaller.__main__.run([
        spec,
        "--noconfirm",
        "--clean",
        f"--distpath=.\\{dist_path}",
    ])

if __name__ == "__main__":
    name = ""
    if len(sys.argv) > 1:
        name = str(sys.argv[1]).lower().strip()

    if name not in ["onefile","file","folder","both"]:
        print("No/Invalid build type selected")
        build_type = quest.select(
            "How should the package be built?",
            choices=[
                'OneFolder',
                'OneFile',
                'both'
            ]).ask()  # returns value of selection
        name = str(build_type).lower()
    print(f"Built type selected: {name}")

    # Check if each package should be built
    if name in ["onefile","file","both"]:
        file()
    if name in ["onefolder","folder","both"]:
        folder()


