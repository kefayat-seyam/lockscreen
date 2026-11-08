[app]
title = LinkScreen
package.name = linkscreen
package.domain = org.linkscreen
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1.0
requirements = python3,kivy
orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 35
android.minapi = 23
android.archs = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1

# Use python-for-android's actively maintained development branch for newer Python runtimes.
p4a.branch = develop
