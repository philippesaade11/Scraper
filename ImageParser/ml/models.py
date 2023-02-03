import torch
import numpy as np
from PIL import Image

from unilm.dit.object_detection.ditod import add_vit_config
from detectron2.config import CfgNode as CN
from detectron2.config import get_cfg
from detectron2.data import MetadataCatalog
from detectron2.engine import DefaultPredictor

from doctr.io.image import read_img_as_tensor
from doctr.models import ocr_predictor

CLASSES = ["text", "title", "list", "table", "figure"]

def get_ocr_model():
    ocr_model = ocr_predictor(pretrained=True)
    return ocr_model

def get_detector_model():
    detector_cfg = get_cfg()
    add_vit_config(detector_cfg)
    detector_cfg.merge_from_file("/app/ml/cascade_dit_base.yml")
    detector_cfg.MODEL.WEIGHTS = "/app/ml/publaynet_dit-b_cascade.pth"
    detector_cfg.MODEL.DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

    md = MetadataCatalog.get(detector_cfg.DATASETS.TEST[0])
    md.set(thing_classes=CLASSES)
    detector_model = DefaultPredictor(detector_cfg)
    return detector_model

def get_detector_output(model, img_path):
    img = np.array(Image.open(img_path))

    with torch.no_grad():
        output = model(img)["instances"]
    return {'classes': output.pred_classes.tolist(),
            'boxes': output.pred_boxes.tensor.tolist()}

def get_ocr_output(model, img_path):
    img = read_img_as_tensor(img_path).unsqueeze(0)

    with torch.no_grad():
        output = model(img).export()
    return output

if __name__ == '__main__':
    get_ocr_model()
    get_detector_model()
