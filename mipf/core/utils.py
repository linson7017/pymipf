from vtkmodules.vtkIOImage import vtkNIFTIImageReader, vtkMetaImageReader
from vtkmodules.vtkIOXML import vtkXMLPolyDataReader, vtkXMLImageDataReader
from vtkmodules.vtkIOGeometry import vtkSTLReader



def load_image(filename: str):
    if filename.endswith('nii') or filename.endswith('nii.gz'):
        reader = vtkNIFTIImageReader()
        reader.SetFileName(filename)
        reader.Update()
        return reader.GetOutput()
    if filename.endswith('vti'):
        reader = vtkXMLImageDataReader()
        reader.SetFileName(filename)
        reader.Update()
        return reader.GetOutput()
    if filename.endswith('mha'):
        reader = vtkMetaImageReader()
        reader.SetFileName(filename)
        reader.Update()
        return reader.GetOutput()
    else:
        return None


def load_surface(filename: str):
    if filename.endswith('vtp'):
        reader = vtkXMLPolyDataReader()
        reader.SetFileName(filename)
        reader.Update()
        return reader.GetOutput()
    elif filename.endswith('stl'):
        reader = vtkSTLReader()
        reader.SetFileName(filename)
        reader.Update()
        return reader.GetOutput()
    else:
        return None


def hex_to_float(hex_color):
    """
    将十六进制颜色字符串转换为浮点格式。
    支持 #RRGGBB 和 #RRGGBBAA 格式。
    """
    hex_color = hex_color.lstrip("#")  # 去掉 '#' 前缀
    if len(hex_color) == 6:  # RGB 格式
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return r / 255.0, g / 255.0, b / 255.0
    elif len(hex_color) == 8:  # RGBA 格式
        r, g, b, a = (
            int(hex_color[0:2], 16),
            int(hex_color[2:4], 16),
            int(hex_color[4:6], 16),
            int(hex_color[6:8], 16),
        )
        return r / 255.0, g / 255.0, b / 255.0, a / 255.0
    else:
        raise ValueError("Invalid hex color format. Expected #RRGGBB or #RRGGBBAA.")
