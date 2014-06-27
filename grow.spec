# -*- mode: python -*-

a = Analysis(['bin/grow'],
             pathex=['.', '../grow', '../env/lib/python2.7/site-packages/'],
             hiddenimports=[
                'babel.numbers',
                'babel.plural',
                'markdown',
                'markdown.extensions',
                'werkzeug',
                'werkzeug._internal',
                'werkzeug.datastructures',
                'werkzeug.debug',
                'werkzeug.exceptions',
                'werkzeug.formparser',
                'werkzeug.http',
                'werkzeug.local',
                'werkzeug.routing',
                'werkzeug.script',
                'werkzeug.security',
                'werkzeug.serving',
                'werkzeug.test',
                'werkzeug.testapp',
                'werkzeug.urls',
                'werkzeug.useragents',
                'werkzeug.utils',
                'werkzeug.wrappers',
                'werkzeug.wsgi',
             ],
             hookspath=None,
             runtime_hooks=None)

a.datas += [
    ('VERSION', 'grow/VERSION', 'DATA'),
    ('server/templates/error.html', 'grow/server/templates/error.html', 'DATA'),
    ('deployments/data/cacerts.txt', 'grow/deployments/data/cacerts.txt', 'DATA'),
    ('closure/closure.jar', 'env/lib/python2.7/site-packages/closure/closure.jar', 'DATA'),
    ('pods/preprocessors/closure_lib/closurebuilder.py', 'grow/pods/preprocessors/closure_lib/closurebuilder.py', 'DATA'),
    ('pods/preprocessors/closure_lib/depstree.py', 'grow/pods/preprocessors/closure_lib/depstree.py', 'DATA'),
    ('pods/preprocessors/closure_lib/jscompiler.py', 'grow/pods/preprocessors/closure_lib/jscompiler.py', 'DATA'),
    ('pods/preprocessors/closure_lib/source.py', 'grow/pods/preprocessors/closure_lib/source.py', 'DATA'),
    ('pods/preprocessors/closure_lib/treescan.py', 'grow/pods/preprocessors/closure_lib/treescan.py', 'DATA'),
]

pyz = PYZ(a.pure)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='grow',
          debug=False,
          strip=None,
          upx=True,
          console=True)

#coll = COLLECT(exe,
#               a.binaries,
#               a.zipfiles,
#               a.datas,
#               strip=None,
#               upx=True,
#               name='dist/grow.coll')
#app = BUNDLE(coll,
#             version=open('pygrow/grow/VERSION').read(),
#             name='dist/grow.app',
#             icon='macgrow/icon.icns')
