import numpy as np
from ultralytics import YOLO
import cv2

import util

from tracker import Tracker
from util import get_car, read_license_plate, write_csv

results = {}

tracker = Tracker()

# load models
coco_model = YOLO('yolov9e.pt')
license_plate_detector = YOLO('models/license_plate_detector.pt')

# load video
cap = cv2.VideoCapture('./sample.mp4')

vehicles = [2, 3, 5, 7]

############################ add dictionary
coco_names = {
    2: "CAR",
    3: "BIKE",
    5: "BUS",
    7: "TRUCK"
}
#############################

# read frames
frame_nmr = -1
ret = True
while ret:
    frame_nmr += 1
    ret, frame = cap.read()
    if ret:
        results[frame_nmr] = {}
        # detect vehicles
        detections = coco_model(frame)[0]
        detections_ = []
        track_ids = []
        score = 0
        track_id=0
        for detection in detections.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = detection
            if int(class_id) in vehicles:
                class_name = coco_names[int(class_id)]
                detections_.append([x1, y1, x2, y2, score])
        print(detections_)
        # track vehicles
        # track_ids = mot_tracker.update(np.asarray(detections_))

        tracker.update(frame,np.asarray(detections_))
        for track in tracker.tracks:
            bbox = track.bbox
            x1, y1, x2, y2 = bbox
            track_id = track.track_id
            track_ids.append([x1, y1, x2, y2,score,track_id])

        print(track_ids)

        # detect license plates
        license_plates = license_plate_detector(frame)[0]

        for license_plate in license_plates.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = license_plate
            print(x1, y1, x2, y2, score, class_id)
            # assign license plate to car
            xcar1, ycar1, xcar2, ycar2, car_score, car_id = get_car(license_plate, track_ids)

            if car_id != -1:
                if int(class_id) in vehicles:
                    class_name = coco_names[int(class_id)]

                # crop license plate
                license_plate_crop = frame[int(y1):int(y2), int(x1): int(x2), :]

                # process license plate
                license_plate_crop_gray = cv2.cvtColor(license_plate_crop, cv2.COLOR_BGR2GRAY)
                _, license_plate_crop_thresh = cv2.threshold(license_plate_crop_gray, 64, 255, cv2.THRESH_BINARY_INV)

                # read license plate number
                license_plate_text, license_plate_text_score = read_license_plate(license_plate_crop_thresh)

                if license_plate_text is not None:
                    results[frame_nmr][car_id] = {'class_name': class_name,
                                                  'car': {'bbox': [xcar1, ycar1, xcar2, ycar2],
                                                          'score': car_score, },
                                                  'license_plate': {'bbox': [x1, y1, x2, y2],
                                                                    'text': license_plate_text,
                                                                    'bbox_score': score,
                                                                    'text_score': license_plate_text_score}}

# write results
write_csv(results, './test.csv')
