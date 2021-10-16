import os
import shutil
import glob
import time
import typing
import sys

import cv2
import img2pdf
import argparse

from multiprocessing import Pool, cpu_count
from tqdm import tqdm
from math import ceil

from skimage.metrics import structural_similarity


def save_frame(frame, path, frame_id):
    filename = path + "/frame_" + \
        str(int(time.time())) + '_' + str(int(frame_id)) + ".jpg"
    cv2.imwrite(filename, frame)


def get_video_paths(root_dir: str):
    if not os.path.exists(root_dir):
        print("Directory not found, please enter valid directory..")
        sys.exit(1)

    paths = []
    for rootDir, directory, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith(('.mp4')):
                paths.append(os.path.join(rootDir, filename))

    return paths


def extract_slides_from_vid(video_path: str, threshold: float, save_initial: bool, capture_frequency: int, slide_bounds: typing.List[int], temp_captures_path: str, output_path: str, position: int):

    video_name = os.path.splitext(os.path.basename(video_path))[0]

    video_folder = os.path.join(temp_captures_path, video_name)

    pdf_path = os.path.join(output_path, video_name) + '.pdf'

    if not os.path.exists(video_folder):
        os.mkdir(video_folder)

    capture = cv2.VideoCapture(video_path)

    frame_rate = capture.get(cv2.CAP_PROP_FPS)
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_skip = int(capture_frequency * frame_rate)
    eval_count = int(frame_count / frame_skip)

    prev_frame = None

    bar = tqdm(total=eval_count, position=position)

    try:
        while capture.isOpened():
            frame_id = capture.get(cv2.CAP_PROP_POS_FRAMES)

            ret, frame = capture.read()

            if not ret:
                break

            frame = frame[slide_bounds[1]:slide_bounds[3],
                        slide_bounds[0]:slide_bounds[2], :]

            if prev_frame is not None:
                prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
                current_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                (score, diff) = structural_similarity(
                    prev_gray, current_gray, full=True)

                if score < threshold:
                    save_frame(frame, video_folder, frame_id)

            elif save_initial:
                save_frame(frame, video_folder, frame_id)

            prev_frame = frame

            bar.update()

            capture.set(cv2.CAP_PROP_POS_FRAMES, min(
                frame_id + frame_skip, frame_count))

        capture.release()
        bar.close()
        bar.clear()

        with open(pdf_path, "wb") as f:
            f.write(img2pdf.convert(glob.glob(video_folder + '/*.jpg')))
        
    except KeyboardInterrupt:
        capture.release()
        bar.close()
        bar.clear()

    shutil.rmtree(video_folder)


def extract_slides_from_batch(process_data: dict):

    threshold = process_data['threshold']
    save_initial = process_data['save_initial']
    slide_bounds = process_data['slide_bounds']
    capture_frequency = process_data['capture_frequency']
    output_path = process_data['output_path']
    temp_captures_path = process_data['temp_captures_path']
    position = process_data['process_id']

    for video in process_data['video_paths']:
        extract_slides_from_vid(
            video, threshold, save_initial, capture_frequency, slide_bounds, temp_captures_path, output_path, position)


def lecture2slides(root_dir: str, threshold: float, processes: int, save_initial: bool, slide_bounds: typing.List[int], output_path: str, capture_frequency: int) -> None:
    if not os.path.exists(root_dir):
        print('Could not find the folder:', root_dir)
        return

    video_paths = get_video_paths(root_dir=root_dir)

    if len(video_paths) == 0:
        print("Found 0 videos. Please enter a directory with images..")
        return

    print("Found {} videos..".format(len(video_paths)))

    if processes > cpu_count():
        print("Number of processes greater than system capacity..")
        processes = cpu_count()
        print("Defaulting to {} parallel processes..".format(processes))

    processes = min(processes, len(video_paths))

    vids_per_process = ceil(len(video_paths)/processes)

    split_paths = []
    for i in range(0, len(video_paths), vids_per_process):
        split_paths.append(video_paths[i:i+vids_per_process])

    temp_captures_path = './frames'

    if not os.path.exists(temp_captures_path):
        os.mkdir(temp_captures_path)

    if not os.path.exists(output_path):
        os.mkdir(output_path)

    split_data = []
    for process_id, batch in enumerate(split_paths):

        process_data = {
            "process_id": process_id,
            "video_paths": batch,
            "threshold": threshold,
            "save_initial": save_initial,
            "slide_bounds": slide_bounds,
            "capture_frequency": capture_frequency,
            "temp_captures_path": temp_captures_path,
            "output_path": output_path
        }

        split_data.append(process_data)

    # Create a pool which can execute more than one process paralelly
    pool = Pool(processes=processes)
    
    try:
        # Map the function
        print("Started {} processes..".format(processes))
        pool.map(extract_slides_from_batch, split_data)

        # Wait until all parallel processes are done and then execute main script
        pool.close()
        pool.join()

    except KeyboardInterrupt:
        pool.close()
        pool.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('root', type=str,
                        help='The path to the folder containing videos')

    parser.add_argument('-t', '--threshold', default=0.85,
                        type=float, help='Similarity threshold to add slide')

    parser.add_argument(
        '-p', "--processes", required=False, type=int, default=cpu_count(), help="Number of parallel processes"
    )

    parser.add_argument('-s', '--save-initial', default=False,
                        help='Save the first frame. (Defaults to false)', action='store_true')

    parser.add_argument('-sl', '--left', default=95, type=int,
                        help='Left coordinate of slide in video')
    parser.add_argument('-st', '--top', default=70, type=int,
                        help='Top coordinate of slide in video')
    parser.add_argument('-sr', '--right', default=865,
                        type=int, help='Right coordinate of slide in video')
    parser.add_argument('-sb', '--bottom', default=650,
                        type=int, help='Bottom coordinate of slide in video')

    parser.add_argument('-o', '--output', type=str, help='The output path')

    parser.add_argument('-f', '--frequency', type=int,
                        default=1, help='Inverse of slide capture frame rate')

    args = parser.parse_args()

    if not args.output:
        args.output = 'slides'

    lecture2slides(args.root, args.threshold, args.processes, args.save_initial, [
                   args.left, args.top, args.right, args.bottom], args.output, args.frequency)
