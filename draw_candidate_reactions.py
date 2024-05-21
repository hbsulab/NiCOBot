# import cv2
import subprocess
import numpy as np
from rxnmapper import RXNMapper
from PIL import Image
from rdkit import Chem
from io import BytesIO
from rdkit.Chem import AllChem
from rdkit.Chem.Draw import rdMolDraw2D
from cairosvg import svg2png

def get_rxnmapped_reaction(rxn):
    rxn_mapper = RXNMapper()
    results = rxn_mapper.get_attention_guided_atom_maps([rxn])
    reactants = results[0]['mapped_rxn'].split('>>')[0]
    prod = results[0]['mapped_rxn'].split('>>')[1]

    reactants = Chem.MolFromSmiles(reactants)
    prod = Chem.MolFromSmiles(prod)
    max_index = max([int(a.GetProp('molAtomMapNumber')) for a in reactants.GetAtoms() 
                    if 'molAtomMapNumber' in a.GetPropsAsDict()])
    unmapped_atoms = [a for a in reactants.GetAtoms() 
                    if 'molAtomMapNumber' not in a.GetPropsAsDict()]
    [a.SetProp('molAtomMapNumber', str(max_index + i + 1)) \
        for (i, a) in enumerate(unmapped_atoms) \
        if 'molAtomMapNumber' not in a.GetPropsAsDict()]

    prod.UpdatePropertyCache()
    Chem.SanitizeMol(prod)

    rxn_new = Chem.MolToSmiles(reactants).split('.')[1] + '.' + Chem.MolToSmiles(reactants).split('.')[0] + '>>' + Chem.MolToSmiles(prod)

    return rxn_new

def add_text_to_image(image, text, position, font_scale, font=cv2.FONT_HERSHEY_SIMPLEX, color=(0, 0, 0), thickness=1, line_type=cv2.LINE_AA):
    cv2.putText(image, text, position, font, font_scale, color, thickness, line_type)

def get_reaction_image_small(rxn_smiles):
    rxn = AllChem.ReactionFromSmarts(rxn_smiles, useSmiles=True)
    colors = [(0.3, 0.7, 0.9), (0.9, 0.7, 0.9), (0.6, 0.9, 0.3), (0.9, 0.9, 0.1)]
    # colors = [(1, 1, 1), (1, 1, 1), (1, 1, 1), (1, 1, 1)]
    d = rdMolDraw2D.MolDraw2DSVG(600, 100)
    d.DrawReaction(rxn, highlightByReactant=True, highlightColorsReactants=colors)
    d.FinishDrawing()

    svg = d.GetDrawingText().replace('svg:', '')
    reaction_image = svg2png(bytestring=svg.encode('utf-8'))

    reaction_image = Image.open(BytesIO(reaction_image))
    reaction_image = cv2.cvtColor(np.array(reaction_image), cv2.COLOR_RGB2BGR)

    return reaction_image

def save_images(all_reactions_dict, dict_path):
    for target_smiles, ref_smiles_dict in all_reactions_dict.items():
        images = []
        for ref_smiles, reaction_details in ref_smiles_dict.items():
            sim_score = reaction_details[0]['sim_score']
            for i in range(len(reaction_details[0]['conds_sum'])):
                conds_sum = reaction_details[0]['conds_sum'][i]
                yields= reaction_details[0]['yields'][i]
                doi= reaction_details[0]['doi'][i]
                rxn_origin = reaction_details[0]['rxn_origin'][i]
                if len(rxn_origin) != 0:
                    rxn_new = reaction_details[0]['rxn_new'][i]

                    rxn_new = get_rxnmapped_reaction(rxn_new)

                    rxn_new_image = get_reaction_image_small(rxn_new)
                    rxn_new_image = cv2.cvtColor(rxn_new_image, cv2.COLOR_BGR2RGB)

                    score_text_position = (100,10)
                    add_text_to_image(rxn_new_image, sim_score, score_text_position, 0.3)

                    conds_text_position = (100, 98)
                    add_text_to_image(rxn_new_image, conds_sum, conds_text_position, 0.3)

                    # images.append(Image.fromarray(rxn_new_image))

                    # if type(lig_smiles) == str:
                    #     rxn_smiles_origin = insert_string_between_arrows(rxn_smiles, lig_smiles)
                    # else:
                    #     rxn_smiles_origin = rxn_smiles
                    
                    rxn_origin_image = get_reaction_image_small(rxn_origin)
                    rxn_origin_image = cv2.cvtColor(rxn_origin_image, cv2.COLOR_BGR2RGB)
                    conds_text_position = (100, 98)
                    add_text_to_image(rxn_origin_image, conds_sum, conds_text_position, 0.3)

                    yields_text_position = (450, 10)
                    add_text_to_image(rxn_origin_image, yields, yields_text_position, 0.3)

                    doi_text_position = (250, 10)
                    add_text_to_image(rxn_origin_image, doi, doi_text_position, 0.3)

                    rxn_new_and_origin_image = np.hstack((rxn_new_image, rxn_origin_image))

                    images.append(Image.fromarray(rxn_new_and_origin_image))

        if len(images) != 0:
            concatenated_image = Image.new('RGB', (images[0].width, sum(img.height for img in images)))

            y_offset = 0
            for img in images:
                concatenated_image.paste(img, (0, y_offset))
                y_offset += img.height
            

            png_path = dict_path + '/' + target_smiles + '_' + str(i) + '.png'

            concatenated_image.save(png_path)

            pbm_path = dict_path + '/' + target_smiles + '_' + str(i) + '.pbm'
            svg_path = dict_path + '/' + target_smiles + '_' + str(i) + '.svg'

            subprocess.run(['convert', png_path, pbm_path])
            subprocess.run(['potrace', '-s', pbm_path, '-o', svg_path])
            subprocess.run(['rm', pbm_path])