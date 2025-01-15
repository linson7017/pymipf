# MIPF

MIPF (Medical Image Processing Framework) is a python library based on [trame](https://github.com/Kitware/trame), primarily designed for medical image processing and visualization. Its architecture is inspired by [MITK(Medical Imaging Interaction Toolkit)](https://github.com/MITK/MITK)  and supports loading, browsing, and interacting with medical imaging data.

1. Build:
### Linux
```console
python setup.py bdist_wheel -p linux_x86_64
```
### Windows
```console
python setup.py bdist_wheel -p win_amd64
```

2. Install:
```console
pip install ./dist/mipf-**.whl
```

3. Run a web application:
```console
workbench -f "your image(*.vti,*.nii,*.mha) or model(*.vtp,*.stl,*.ply) filepath" --port "port" --host 'host ip' --server
```


These are some simple examples and more features are under development.
![MutliViews](./imgs/multi_view.png)
![Model](./imgs/model.png)
![VolumeRendering](./imgs/volume.png)
![Slice](./imgs/slice.png)