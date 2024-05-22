import requests
import os

def cdk(smiles):
    """
    Get a depiction of some smiles.
    """

    url = "https://www.simolecule.com/cdkdepict/depict/wob/svg"
    headers = {"Content-Type": "application/json"}
    response = requests.get(
        url,
        headers=headers,
        params={
            "smi": smiles,
            "annotate": "colmap",
            "zoom": 2,
            "w": 150,
            "h": 80,
            "abbr": "off",
        },
    )
    return response.text

def get_image_path_from_folder(folder_path: str):
    image_extensions = ['.png']  # 支持的图片文件扩展名
    image_path = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if os.path.splitext(f)[1].lower() in image_extensions][0]
    return image_path
