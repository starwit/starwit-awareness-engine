import shutil
import argparse
import os
import sys
from pathlib import Path
from typing import List

import cv2
import tqdm
from numpy.typing import NDArray


def get_image_files(path: Path) -> List[Path]:
    files = os.listdir(path)
    image_files = [path / f for f in files if f.split('.')[-1].lower() in ('jpg', 'jpeg')]
    return image_files

def load_image(path: Path) -> NDArray:
    return cv2.imread(path, cv2.IMREAD_COLOR)

def load_mask(path: Path) -> NDArray:
    mask_img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    # Mask needs to be inverted, b/c of how cv2.substract masking works
    return 255 - mask_img

def save_image(image: NDArray, path: Path) -> None:
    cv2.imwrite(path, image)

def overlay_mask(image: NDArray, mask: NDArray) -> None:
    cv2.subtract(src1=image, src2=image, dst=image, mask=mask)

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-m', '--mask', type=Path, required=True, help='A mask to overlay onto all images. Black (brightness == 0) areas will be removed / blackened.')
    argparser.add_argument('image_path', type=Path, help='Path to a directory of images that should be processed')
    args = argparser.parse_args()

    mask = load_mask(args.mask)
    image_paths = get_image_files(args.image_path)
    original_files_path = args.image_path / 'original_files'

    os.makedirs(original_files_path, exist_ok=True)

    for image_path in tqdm.tqdm(image_paths):
        img = load_image(image_path)
        if img.shape[:2] != mask.shape[:2]:
            print(f'{image_path.name} has different shape than mask {args.mask.name}. Skipping...', file=sys.stderr)
            continue
        overlay_mask(img, mask)
        shutil.move(image_path, original_files_path / image_path.name)
        save_image(img, image_path)
