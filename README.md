# Lecture2Slides

## About

Convert lecture videos to slides in one line. Takes an input of a directory containing your lecture videos and outputs a directory containing .PDF files containing the slides of each lecture. (You can download the videos from Google Drive even if you only have View-Only permissions. Google it)


The utility only captures slides when it detects that a slide has changed and does not capture every frame. Thus your pdf will be very close to the actual slides used. (If you find that slides are being repeated due to being written on, try reducing the threshold as detailed below). You can also automatically run OCR on the resulting PDF files to make your slides searchable and copy/paste-able

## Features

- Convert a video file into a .PDF of the respective slides
- MultiProcessing for parallel conversion of videos in an folder
- Progress Indication and approximate ETA
- Run automatic OCR on slides and save a text layer to the resulting PDF

## Running

This program requires [python](https://www.python.org/downloads/) to run. Additionaly you also need to have installed [OpenCV](https://opencv.org/releases/) and have your path configured correctly.

- Clone the repo
- Install requirements using `pip install -r requirements.txt`
- Run the program `python main.py <videos_folder_name>`

OCR is disabled by default. If you want to run OCR you must also install [tesseract](https://github.com/tesseract-ocr/tesseract) and [GhostScript](https://ghostscript.com/) and configure your path with these as well

 - To run the program with OCR simply use the `--ocr` flag (`python main.py --ocr <videos_folder_name>`)

## Options

The program provides many command line options to customize the execution

    -h, --help                           Print this help text and exit

    -t, --threshold                      Similarity threshold to add slide

    -p, --processes                      Number of parallel processes

    -s, --save-initial                   Use this option if you find the first
                                         slide from the video is missing

    -sl, --left                          The left coordinate of the slide in the video
    -st, --top                           The top coordinate of the slide in the video
    -sr, --right                         The right coordinate of the slide in the video
    -sb, --bottom                        The bottom coordinate of the slide in the video

    -o, --output                         The folder to store the slides in

    -f, --frequency                      How many seconds elapse before a frame is
                                         processed
    
    --ocr                                Run OCR to make the resulting PDF searchable

### Note
- The slide coordinates are configured by default for the standard presentation size for a 720p Google Meet recording.
- Increasing the frequency improves performance
- If you find slides being repeated due to writing, reduce the threshold. We find that the sweet spot is between 0.82 to 0.85. (Do not set it below 0.8 as it will omit almost every slide. Conversely, setting it above 0.9 will make even tiny changes into a new slide)

## Future updates

Stay tuned for the following updates

 - Automatic video download and conversion from a Google Drive folder link
