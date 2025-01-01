import vtk
import sys
import string


def ReadNii(filename):
    reader = vtk.vtkNIFTIImageReader()
    reader.SetFileName(filename)
    reader.Update()
    return reader.GetOutput()


def ImagePlaneDemo(img):

    # create a window
    window = vtk.vtkRenderWindow()
    
    # create interactor
    interactor = vtk.vtkRenderWindowInteractor()
    window.SetInteractor(interactor)


    
    renderer = vtk.vtkRenderer()
    window.AddRenderer(renderer)
    # create plane source here
    plane_X = vtk.vtkImagePlaneWidget()

    plane_X.SetInteractor(interactor)
    plane_X.SetDefaultRenderer(renderer)
    plane_X.SetCurrentRenderer(renderer)

    plane_X.SetInputData(img)

    plane_X.SetPlaneOrientationToZAxes()

    plane_X.On()


    window.Render()
    interactor.Start()




if __name__ == '__main__':
    #file_name = sys.argv[1]
    file_name = "D:/ncct.nii"
    
    source = ReadNii(file_name)
    ImagePlaneDemo(source)