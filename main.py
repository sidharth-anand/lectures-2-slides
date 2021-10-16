import os
import shutil
import glob
import time
import typing

import cv2
import img2pdf
import argparse
import progressbar

from skimage.metrics import structural_similarity

def save_frame(frame, path, frame_id):
    filename = path + "/frame_" + str(int(time.time())) + '_' + str(int(frame_id)) + ".jpg"
    cv2.imwrite(filename, frame)

def lecture2slides(video_path: str, threshold: float, save_initial: bool, slide_bounds: typing.List[int], output_path: str, capture_frequency: int) -> None:
    if not os.path.exists(video_path):
        print('Could not find the file:', video_path)
        return

    temp_captures_path = './frames_' + video_path[:video_path.find('.')].replace('/', '_').replace('\\', '_')

    if not os.path.exists(temp_captures_path):
        os.mkdir(temp_captures_path)

    capture = cv2.VideoCapture(video_path)

    frame_rate = capture.get(cv2.CAP_PROP_FPS)
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_skip = int(capture_frequency * frame_rate)
    eval_count = int(frame_count / frame_skip)

    prev_frame = None

    print(f'Processing frames in video: {video_path} with capture frequency: {capture_frequency}/sec ...')

    try:
        with progressbar.ProgressBar(max_value=eval_count) as bar:
            while capture.isOpened():
                frame_id = capture.get(cv2.CAP_PROP_POS_FRAMES)

                ret, frame = capture.read()

                if not ret:
                    break

                frame = frame[slide_bounds[1]:slide_bounds[3], slide_bounds[0]:slide_bounds[2], :]

                if prev_frame is not None:
                    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
                    current_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                    (score, diff) = structural_similarity(prev_gray, current_gray, full=True)

                    if score < threshold:
                        save_frame(frame, temp_captures_path, frame_id)
                
                elif save_initial:
                        save_frame(frame, temp_captures_path, frame_id)

                prev_frame = frame

                bar.update(int(frame_id / frame_skip))

                capture.set(cv2.CAP_PROP_POS_FRAMES, min(frame_id + frame_skip, frame_count))

            capture.release()

        print('Collating Slides to PDF...')

        with open(output_path,"wb") as f:
            f.write(img2pdf.convert(glob.glob(temp_captures_path + '/*.jpg')))

        print('Done. Saved to' + output_path)
        
    except KeyboardInterrupt:
        pass
    
    shutil.rmtree(temp_captures_path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('filename', type=str, help='The name of the file to process')

    parser.add_argument('-t', '--threshold', default=0.85, type=float, help='Similarity threshold to add slide')
    parser.add_argument('-s', '--save-initial', default=False, help='Save the first frame. (Defaults to false)', action='store_true')

    parser.add_argument('-sl', '--left', default=95, type=int, help='Left coordinate of slide in video')
    parser.add_argument('-st', '--top', default=70, type=int, help='Top coordinate of slide in video')
    parser.add_argument('-sr', '--right', default=865, type=int, help='Right coordinate of slide in video')
    parser.add_argument('-sb', '--bottom', default=650, type=int, help='Bottom coordinate of slide in video')

    parser.add_argument('-o', '--output', type=str, help='The output path')

    parser.add_argument('-f', '--frequency', type=int, default=1, help='Inverse of slide capture frame rate')

    args = parser.parse_args()

    if not args.output:
        args.output = args.filename[:args.filename.find('.')] + '.pdf'
    
    lecture2slides(args.filename, args.threshold, args.save_initial, [args.left, args.top, args.right, args.bottom], args.output, args.frequency)