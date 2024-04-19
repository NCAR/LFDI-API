import imageio
import os


# @Brief: This function will create a gif from a list of images
# @Param: file_list - list of images to use in the gif
# @Param: save_path - path to save the gif
# @Param: filename - name of the gif
# @Param: delete_files - whether to delete the files after creating the gif
# @Param: setFPS - frames per second of the gif
def createGif(file_list, save_path, filename="Gif.gif", delete_files=False, setFPS=2):
    # make a list of images
    images = []
    for file in file_list:
        images.append(imageio.imread(file))
    
    imageio.mimsave(save_path+"\\" + f'{filename}.gif', images, fps=setFPS)

    # Delete the files
    if delete_files:
        for file in file_list:
            # Check if file exists or if it's a directory
            if os.path.exists(file) and os.path.isfile(file):
                # Delete it
                os.remove(file)
    return