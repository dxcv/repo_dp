# -*- mode: python -*-

block_cipher = None

a = Analysis(['generador.py'],
             pathex=['C:\\Users\\diego\\Desktop\\IM Trust\\generador_presentacion_gestionactivos'],
             binaries=None,
             datas=[],
             hiddenimports=['_mssql'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

def extra_datas(mydir):
   def rec_glob(p, files):
       import os
       import glob
       for d in glob.glob(p):
           if os.path.isfile(d):
               files.append(d)
           rec_glob("%s/*" % d, files)
   files = []
   rec_glob("%s/*" % mydir, files)
   extra_datas = []
   for f in files:
       extra_datas.append((f, f, 'DATA'))

   return extra_datas
###########################################

# append the 'data' dir
a.datas += extra_datas('queries_generador')

# a.datas += [("benchmarkName.sql", "C:\\Users\\diego\\Desktop\\IM Trust\\generador_presentacion_gestionactivos\\queries_generador\\benchmarkName.sql", "DATA")]

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='generador',
          debug=False,
          strip=False,
          upx=True,
          console=True )
