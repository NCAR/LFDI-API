import zwoasi as asi
import os

#Create a Encapsulation class for the ZWO Camera bc the other stuff is too complex
class ZWO_Camera:
    def __init__(self):
        # Find the Library for the ZWO Camera
        asi.init('C:\\Users\\iguser\\Documents\\GitHub\\LFDI_API\\ASI SDK\\lib\\x64\\ASICamera2.dll')
        #Use the First and hopefully the only camera attached to the System
        self.camera = asi.Camera(0)
        self.camera_info = self.camera.get_camera_property()
        self.binning = 1
        self.auto_exposure = False
    
    #Set Exposure in S
    def set_exposure(self, exposure):
        exposure = int(exposure * 1000000)
        self.camera.set_control_value(asi.ASI_EXPOSURE, exposure)
    
    def set_binning(self, binning):
        self.binning = binning
        self.camera.set_roi(bins=binning)


    def set_roi(self, width, height):
        #is the user input 'max' for the width or height set it to the max value
        if width == 'max':
            width = self.camera_info['MaxWidth']
        if height == 'max':
            height = self.camera_info['MaxHeight']

        self.camera.set_roi(width=width, height=height)
    
    
    def set_image_type(self, image_type):
        if image_type == 'RAW8':
            image_type = asi.ASI_IMG_RAW8
        elif image_type == 'RAW16':
            image_type = asi.ASI_IMG_RAW16
        elif image_type == 'RGB24':
            image_type = asi.ASI_IMG_RGB24
        else:
            print('Image type not recognized')
            return
        self.camera.set_image_type(image_type)
        return

    def capture(self, filename):
        self.set_timeout()
        self.camera.set_control_value(asi.ASI_EXPOSURE, self.auto_exposure)
        self.camera.capture(filename=filename)
        return
        
    def set_timeout(self):
        timeout = (self.camera.get_control_value(asi.ASI_EXPOSURE)[0] / 1000) * 2 + 500
        self.camera.default_timeout = timeout
    
    def get_camera_info(self):
        return self.camera_info

    def get_camera_width(self):
        return self.camera.get_roi()[2]
    def get_camera_height(self):
        return self.camera.get_roi()[3]
    def get_camera_image_type(self):
        return self.camera.get_image_type()
    def get_camera_exposure(self):
        return self.camera.get_control_value(asi.ASI_EXPOSURE)[0] / 1000000
    def __str__(self):
        return f"Camera Info: {str(self.camera_info)}\nBinning: {str(self.binning)}\nWidth: {str(self.get_camera_width())}\nHeight: {str(self.get_camera_height())}\n\
            Image Type: {str(self.get_camera_image_type())}\nExposure: {str(self.get_camera_exposure())}\n"
    def set_auto_exposure(self, enable):
        self.auto_exposure = enable
        self.camera.set_control_value(asi.ASI_EXPOSURE, enable)


if __name__ == '__main__':
    #An example of how to use the ZWO Camera Class
    camera = ZWO_Camera()
    print(camera)
    camera.set_exposure(0.1)
    camera.set_binning(2)
    camera.set_image_type('RAW16')
    #camera.set_roi('max', 'max')
    camera.capture('Test_image_Binning2.tiff')
    camera.set_binning(1)
    camera.capture('Test_image_Binning1.tiff')
    print(camera)