[app]
title = buusdo
project_dir =
input_file =
exec_directory = ./dist
project_file =
icon = buusdo/assets/logo.ico

[python]
packages = Nuitka
android_packages = buildozer==1.5.0,cython==0.29.33

[qt]
qml_files =
excluded_qml_plugins =
modules =
plugins =

[android]
wheel_pyside =
wheel_shiboken =
plugins =

[nuitka]
macos.permissions =
mode = onefile
extra_args = --quiet --noinclude-qt-translations --include-package=buusdo --include-package-data=buusdo --include-data-dir=buusdo/locales=buusdo/locales --include-data-dir=buusdo/assets=buusdo/assets

[buildozer]
mode = debug
recipe_dir =
jars_dir =
ndk_path =
sdk_path =
local_libs =
arch =
