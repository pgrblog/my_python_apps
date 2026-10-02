[app]
title = My Python App
package.name = mypythonapp
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,db,csv
source.main = main.py
version = 0.1
requirements = python3,kivy,sqlite3
orientation = portrait
fullscreen = 0
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
