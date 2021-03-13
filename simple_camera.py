import cv2
import time
import os

def gstreamer_pipeline(
    filename='sometestfile.yuv',
    capture_width=3264,
    capture_height=2464,
    display_width=3264/4,
    display_height=2464/4,
    record_width=2464/4,
    record_height=2464/4,
    framerate=21,
    flip_method=0,
):
    return (
        f'nvarguscamerasrc ! ' +
        f'video/x-raw(memory:NVMM),' +
        f'width=(int){int(capture_width)}, height=(int){int(capture_height)},' +
        f'format=(string)NV12, framerate=(fraction){framerate}/1 ! ' +
        f'tee name=t ! ' +
        f'queue ! ' +
        f'nvvidconv ! ' +
        f'video/x-raw, width=(int){int(display_width)}, height=(int){int(display_height)}, format=(string)BGRx ! ' +
        f'videoconvert ! ' +
        f'video/x-raw, format=(string)BGR ! appsink drop=true ' +
        f't. ! ' +
        f'queue ! ' +
        f'nvvidconv ! ' +
        f'video/x-raw, width=(int){int(record_width)}, height=(int){int(record_height)}, format=(string)I420 ! ' +
        f'y4menc ! ' +
        f'filesink location={filename}' + 
        ''
    ).replace('\t', '')

font                   = cv2.FONT_HERSHEY_SIMPLEX
bottomLeftCornerOfText = (2, 14)
fontScale              = 0.5
fontColor              = (255,255,255)
lineType               = 2

def show_camera():
    pipeline = gstreamer_pipeline(flip_method=0)

    while '  ' in pipeline:
        pipeline = pipeline.replace('  ', ' ')

    print('\n', 'Pipeline:\n', pipeline.replace('! ', '!\n'), '\n')
    cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
    cap.read()

    time.sleep(5)

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

        time.sleep(3)

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    os.system('systemctl restart nvargus-daemon')
    time.sleep(5)
    show_camera()
