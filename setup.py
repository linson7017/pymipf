from setuptools import setup, find_packages, Extension
import os, shutil
from setuptools.command.build_py import build_py as build_py_orig
from Cython.Build import cythonize
from Cython.Distutils import build_ext
import versioneer

install_requires = [
    'numpy>=1.12.4',
    'vtk>=9.3.0',
    'trame>=3.7.1',
    'trame-client>=3.5.0',
    'trame-components>=2.4.0',
    'trame-matplotlib>=2.0.3',
    'trame-plotly>=3.0.2',
    'trame-rca>=0.6.0',
    'trame-server>=3.2.3',
    'trame-simput>=2.4.3',
    'trame-vega>=2.1.1',
    'trame-vtk>=2.8.9',
    'trame-vtklocal>=0.6.0',
    'trame-vuetify>=2.6.1',
]

class build_py(build_py_orig):
    def build_packages(self):
        pass

def get_cmds():
    cmds = versioneer.get_cmdclass()
    cmds.update({'build_py': build_py})
    return cmds

ext_modules=[
    Extension('mipf.*',['mipf/*.py']),
    Extension('mipf.core.*',['mipf/core/*.py']),
    Extension('mipf.ui.*',['mipf/ui/*.py']),
    Extension('mipf.apps.*',['mipf/apps/*.py']),
    
]

pakcages = find_packages(exclude=("docs", "examples", "tests"))
v= versioneer.get_version()

#Execute "python setup.py bdist_wheel -p linux_x86_64" on linux.
#Execute "python setup.py bdist_wheel -p win_amd64" on windows. Need VS compiler for ext modules building.
setup(
    name="mipf",
    version=versioneer.get_version(),
    cmdclass=get_cmds(),
    ext_modules=cythonize(ext_modules, language_level='3'),
    #packages=find_packages(exclude=("docs", "examples", "tests")),
    packages=['mipf'],
    include_package_data=True,
    package_data={
        "": ["*.svg"]
        },
    zip_safe=False,
    install_requires=install_requires,
    python_requires="==3.8.*",
    entry_points={
          'console_scripts': [
              'workbench = mipf.apps.workbench:main',
            ]
    }
)
