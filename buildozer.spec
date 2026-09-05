[app]

title = Karanjia Autonomous College
package.name = karanjiaapp
package.domain = org.karanjiacollege

source.dir = .
source.include_exts = py,json,pdf

version = 1.0
requirements = python3==3.11.10,hostpython3==3.11.10,kivy,requests,beautifulsoup4


orientation = portrait

android.permissions = INTERNET

android.archs = arm64-v8a
p4a.branch = master
