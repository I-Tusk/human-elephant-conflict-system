import os                                                                  # To Perform OS level works.
import six
import cv2                                                                 # OpenCV for Computer Vision                                                        # It has a dictionary that contains colors for each label
import argparse                                                            # To get arguments
import collections
import numpy as np
import pyttsx3                                                             # To perform text to speech function
import threading                                                           # To perform multi-threading operations
import playsound                                                           # To play sounds
import tensorflow as tf                                                    # Main Library.
from object_detection.utils import label_map_util                          # To handle label map.
from object_detection.utils import config_util                             # To load model pipeline.
from object_detection.utils import visualization_utils as viz_utils        # To draw rectangles.
from object_detection.builders import model_builder                        # To load & Build models.

#Text to speech setup.
engine = pyttsx3.init()
en_voice_id = "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0"  # female
ru_voice_id = "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_RU-RU_IRINA_11.0"  # male
engine.setProperty('voice', en_voice_id)
rate = engine.getProperty('rate')
engine.setProperty('rate', rate - 25)


def talk_function(text):               # Text to speech convertion
    print("Computer: {}".format(text))
    engine.say(text)
    engine.runAndWait()

# Enable GPU dynamic memory allocation
gpus = tf.config.experimental.list_physical_devices('GPU')
for gpu in gpus:
    tf.config.experimental.set_memory_growth(gpu, True)


model_config_path =  f'data/models/ssd_mobilenet_v2_320x320_coco17_tpu-8/pipeline.config'        # Store the path of config file
checkpoint_model_path   =  f'data/models/ssd_mobilenet_v2_320x320_coco17_tpu-8/checkpoint/ckpt-0'      # Store the path of model
label_map_path    =  f'data/mscoco_label_map.pbtxt'                             # Store the path of label_map


# Load pipeline config and build a detection model
configs = config_util.get_configs_from_pipeline_file(model_config_path)
model_config = configs['model']
detection_model = model_builder.build(model_config=model_config, is_training=False)

# Restore checkpoint
ckpt = tf.compat.v2.train.Checkpoint(model=detection_model)
ckpt.restore(checkpoint_model_path).expect_partial()

@tf.function

def detect_fn(image):
    """Detect objects in image."""

    image, shapes = detection_model.preprocess(image)
    prediction_dict = detection_model.predict(image, shapes)
    detections = detection_model.postprocess(prediction_dict, shapes)

    return detections, prediction_dict, tf.reshape(shapes, [-1])


category_index = label_map_util.create_category_index_from_labelmap(label_map_path,
                                                                    use_display_name=True)

cap = cv2.VideoCapture("test-video.m4v")

while True:
    # Read frame from camera
    ret, image_np = cap.read()

    # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
    image_np_expanded = np.expand_dims(image_np, axis=0)

    # Things to try:
    # Flip horizontally
    # image_np = np.fliplr(image_np).copy()

    # Convert image to grayscale
    # image_np = np.tile(
    #     np.mean(image_np, 2, keepdims=True), (1, 1, 3)).astype(np.uint8)

    input_tensor = tf.convert_to_tensor(np.expand_dims(image_np, 0), dtype=tf.float32)
    detections, predictions_dict, shapes = detect_fn(input_tensor)

    label_id_offset = 1
    image_np_with_detections = image_np.copy()

    min_score_thresh = 0.50

    box_to_display_str_map = collections.defaultdict(list)
    box_to_color_map = collections.defaultdict(str)

    number_of_items = 0

    for i in range(detections['detection_boxes'][0].numpy().shape[0]):
        
        if detections['detection_scores'][0].numpy() is None or detections['detection_scores'][0].numpy()[i] > min_score_thresh:
            
            box = tuple(detections['detection_boxes'][0].numpy()[i].tolist())

            display_str = ""

            if(detections['detection_classes'][0].numpy() + label_id_offset).astype(int)[i] in six.viewkeys(category_index):
                class_name = category_index[(detections['detection_classes'][0].numpy() + label_id_offset).astype(int)[i]]['name']
                display_str = '{}'.format(class_name)

                box_to_display_str_map[box].append(display_str) # Join the number of eleements with label Name



    im_width, im_height = image_np.shape[1::-1]

    for box, color in box_to_display_str_map.items():
        ymin, xmin, ymax, xmax = box

        ymin = ymin * im_height
        xmin = xmin * im_width
        ymax = ymax * im_height
        xmax = xmax * im_width

        x = xmin
        y = ymin
        w = xmax - xmin
        h = ymax - ymin

        if box_to_display_str_map[box][0].replace("_"," ") == "elephant": # Get only label name not the total number of items

            cv2.rectangle(image_np_with_detections, (int(x),int(y)), (int(x) + int(w), int(y) + int(h)), (0, 0, 255), 4)

            (tw, th), _ = cv2.getTextSize(box_to_display_str_map[box][0], cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)

            # Prints the text.
            img = cv2.rectangle(image_np_with_detections, (int(x), int(y) - 30), (int(x) + 20 + tw, int(y)), (0, 0, 255), -1)
            img = cv2.putText(image_np_with_detections, box_to_display_str_map[box][0].upper(), (int(x)+5, int(y) - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,0), 2)


    # Display output
    cv2.imshow('object detection', cv2.resize(image_np_with_detections, (800, 600)))

    if cv2.waitKey(25) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
