from detect_sample_as_runPipeline import runPipeline
from detect_sample_as_runPipeline import SampleRecognition
import argparse
import cv2

def main():
    # Construct the argument parser and parse the arguments.
    ap = argparse.ArgumentParser()
    ap.add_argument("--image_dir", type=str)
    args = vars(ap.parse_args())

    ##** CHANGE the next two lines for the file and/or alliance you want to test. **
    image_filename = "LRS0308173523970710581193948.png"
    alliance = "RED"

    # load the image
    image_full_path = args["image_dir"] + image_filename
    src = cv2.imread(image_full_path)
    if src is None:
        print('File not found')
        return

    alliance_instance = SampleRecognition.Alliance[alliance]

    _, result_image, lloutput = runPipeline(src, [alliance_instance.value])
    print(lloutput)

    # show the image
    cv2.imshow(alliance + " alliance samples" , result_image)
    cv2.waitKey(0)


if __name__ == "__main__":
    main()