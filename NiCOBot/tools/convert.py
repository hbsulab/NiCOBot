import os
import shutil
import subprocess
import json
import requests
from langchain.tools import BaseTool

def extract_smiles_from_screenshot_MolGrapher(molecule_images_dir):

    source_folder = molecule_images_dir
    target_folder = '/home/zhujingyuan/MolGrapher/data/benchmarks/default/images'

    for file_name in os.listdir(source_folder):
        source_file = os.path.join(source_folder, file_name)
        target_file = os.path.join(target_folder, file_name)
        if os.path.isfile(source_file):
            shutil.copy(source_file, target_file)

    command = 'bash /home/zhujingyuan/MolGrapher/molgrapher/scripts/annotate/run.sh'
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    process.wait()
    print('SMILES extracted succeeded.')

    smiles_label_dict = {}
    smiles_jsonl = '/home/zhujingyuan/MolGrapher/data/predictions/molgrapher/default/smiles.jsonl'
    with open(smiles_jsonl, 'r') as json_file:
        for line in json_file:
            mol_data = json.loads(line.strip())
            smiles = mol_data['smi']
            label = mol_data['file-info']['filename'].split('/')[-1].split('.')[0]
            smiles_label_dict[label] = smiles
    
    with open('Data_Output/' + 'SMILES.json', 'w') as json_file:
        json.dump(smiles_label_dict, json_file, indent=4)
    
    return smiles_label_dict

class Image2SMILES(BaseTool):
    name = "Image2SMILES"
    description = "Check if there are any files in Molcule_Images folder; if there are, convert them to SMILES."

    def _run(self, query) -> str:
        """Converts images to SMILES."""
        molecule_images_dir = 'Molcule_Images'
        if os.path.exists(molecule_images_dir):
            smiles_label_dict = extract_smiles_from_screenshot_MolGrapher(molecule_images_dir)
            return smiles_label_dict
        else:
            return "No images to convert."

class JSON2SMILES(BaseTool):
    name = "JSON2SMILES"
    description = "Input JSON data, convert the molecule names in this JSON to SMILES."

    def _run(self, query) -> str:
        molecule_keys = ["substrate 1", "substrate 2", "product", "ligand", "base", "solvent", "additive"]
        print(query)
        query = json.loads(query)
        for entry in query[0]['Entries']:
            for key in entry:
                if key in molecule_keys:
                    url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{}/{}"
                    r = requests.get(url.format(entry[key], "property/IsomericSMILES/JSON"))
                    data = r.json()
                    try:
                        smi = data["PropertyTable"]["Properties"][0]["IsomericSMILES"]
                        entry[key] = smi
                    except KeyError:
                        entry[key] = f"No SMILES found for {entry[key]}"
                        
        return query