from pipeline import Pipeline

import cv2
import time
import os

pipeline = Pipeline(
    display_size=(3264/2, 2464/2),
    recording_size=(3264/4, 2464/4),
    filename='fisk.yuv'
)

font                   = cv2.FONT_HERSHEY_SIMPLEX
bottomLeftCornerOfText = (2, 14)
fontScale              = 0.5
fontColor              = (255,255,255)
lineType               = 2

def show_camera():
    print(pipeline.get_string())
    cap = cv2.VideoCapture(pipeline.get_string(), cv2.CAP_GSTREAMER)
    cap.read()

    if cap.isOpened():
        window_handle = cv2.namedWindow("CSI Camera", cv2.WINDOW_AUTOSIZE)

        then = time.time()
        start = then

        fps = 21

        while cv2.getWindowProperty("CSI Camera", 0) >= 0:
            ret_val, img = cap.read()

            now = time.time()
            fps = fps * 0.95 + 0.05 * 1 / (now - then)
            cv2.putText(img,f'{fps:.2f} fps', 
                bottomLeftCornerOfText, 
                font, 
                fontScale,
                fontColor,
                lineType)
            then = now

            cv2.imshow("CSI Camera", img)
            
            keyCode = cv2.waitKey(30) & 0xFF
            
            if keyCode == 27:
                break

            if now - start > 8:
                break

    else:
        print("Unable to open camera")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    show_camera()
