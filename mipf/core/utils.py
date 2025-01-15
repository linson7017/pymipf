from vtkmodules.vtkIOImage import (
    vtkNIFTIImageReader,
    vtkMetaImageReader,
    vtkNIFTIImageWriter,
    vtkMetaImageWriter)
from vtkmodules.vtkIOXML import (
    vtkXMLPolyDataReader,
    vtkXMLImageDataReader,
    vtkXMLPolyDataWriter,
    vtkXMLImageDataWriter)
from vtkmodules.vtkIOGeometry import (
    vtkSTLReader,
    vtkSTLWriter
)
from vtkmodules.vtkCommonDataModel import (
    vtkImageData,
    vtkPolyData
)


def load_image(filename: str) -> vtkImageData:
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


def load_surface(filename: str) -> vtkPolyData:
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


def save_image(image: vtkImageData, filename: str):
    if filename.endswith('nii') or filename.endswith('nii.gz'):
        writer = vtkNIFTIImageWriter()
        writer.SetInputData(image)
        writer.SetFileName(filename)
        writer.Update()
    if filename.endswith('vti'):
        writer = vtkXMLImageDataWriter()
        writer.SetInputData(image)
        writer.SetFileName(filename)
        writer.Update()
    if filename.endswith('mha'):
        writer = vtkMetaImageWriter()
        writer.SetInputData(image)
        writer.SetFileName(filename)
        writer.Update()
    else:
        raise ValueError(f"Unsupported image file type:{filename}")


def save_surface(polydata: vtkPolyData, filename: str) -> vtkPolyData:
    if filename.endswith('vtp'):
        writer = vtkXMLPolyDataWriter()
        writer.SetFileName(filename)
        writer.Update()
        return writer.GetOutput()
    elif filename.endswith('stl'):
        writer = vtkSTLWriter()
        writer.SetFileName(filename)
        writer.Update()
        return writer.GetOutput()
    else:
        raise ValueError(f"Unsupported Surface file type:{filename}")


def hex_to_float(hex_color):
    """
    Convert color string from hex to rgba int float type。
    """
    hex_color = hex_color.lstrip("#")  # 去掉 '#' 前缀
    if len(hex_color) == 6:  # RGB 格式
        r, g, b = int(hex_color[0:2], 16), int(
            hex_color[2:4], 16), int(hex_color[4:6], 16)
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
        raise ValueError(
            "Invalid hex color format. Expected #RRGGBB or #RRGGBBAA.")


def float_to_hex(float_color):
    if len(float_color) == 3:
        float_color += [1.0]
    if len(float_color) == 4:
        r, g, b, a = float_color
        r = int(r * 255)
        g = int(g * 255)
        b = int(b * 255)
        a = int(a * 255)
        hex_color = f'#{r:02X}{g:02X}{b:02X}{a:02X}'
        return hex_color
    else:
        raise ValueError("Color should be rgb or rgba format!")


def extract_tf(xml_data):
    import xml.etree.ElementTree as ET
    # 解析 XML 字符串
    root = ET.fromstring(xml_data)

    # 提取 ScalarOpacity 中的点
    scalar_opacity = []
    for point in root.find('ScalarOpacity').iter('point'):
        x = float(point.get('x'))
        y = float(point.get('y'))
        scalar_opacity.append((x, y))

    # 提取 GradientOpacity 中的点
    gradient_opacity = []
    for point in root.find('GradientOpacity').iter('point'):
        x = float(point.get('x'))
        y = float(point.get('y'))
        gradient_opacity.append((x, y))

    # 提取 Color 中的点
    color = []
    for point in root.find('Color').iter('point'):
        x = float(point.get('x'))
        r = float(point.get('r'))
        g = float(point.get('g'))
        b = float(point.get('b'))
        midpoint = float(point.get('midpoint'))
        sharpness = float(point.get('sharpness'))
        color.append((x, r, g, b, midpoint, sharpness))

    return scalar_opacity, gradient_opacity, color


def bounds_union(*bounds_list):
    vinf = float("inf")
    xmin, xmax = vinf, -vinf
    ymin, ymax = vinf, -vinf
    zmin, zmax = vinf, -vinf

    # 遍历所有 bounds 并计算并集
    for bounds in bounds_list:
        xmin = min(xmin, bounds[0])
        xmax = max(xmax, bounds[1])
        ymin = min(ymin, bounds[2])
        ymax = max(ymax, bounds[3])
        zmin = min(zmin, bounds[4])
        zmax = max(zmax, bounds[5])

    return (xmin, xmax, ymin, ymax, zmin, zmax)
