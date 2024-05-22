import re
import pandas as pd
from rxnmapper import RXNMapper
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem import DataStructs
from generate_retro_templates import process_an_example
from generate_product_by_connect_E_Nu import *
# from draw_candidate_reactions import *

def format_conditions(condition_str):
    # conditions_list = condition_str.split('.')
    conditions_list = re.findall(r'\[[^\]]*?\]', condition_str)

    formatted_conditions = []
    temperature_condition = ''
    hours_condition = ''
    for condition in conditions_list:

        condition = condition.strip('[]')
        if "•" in condition:
            condition = condition.replace("•", ".")

        if '掳C' in condition:
            condition = condition.replace("掳C", "-T")
            temperature_condition = condition
        elif '-H' in condition:
            condition = re.split(r'[\(\)]', condition)
            condition = [item for item in condition if item]
            formatted_conditions.append(condition[0])
            hours_condition = condition[-1]
        else:
            formatted_conditions.append(condition)

    formatted_conditions.append(temperature_condition)
    formatted_conditions.append(hours_condition)

    formatted_sentence = 'Conditions: ' + ' '.join(formatted_conditions)
    
    return formatted_sentence

def calculate_similarity(smiles, smiles_list):
    query_molecule = Chem.MolFromSmiles(smiles)
    molecules = [Chem.MolFromSmiles(s) for s in smiles_list]
    query_fp = AllChem.GetMorganFingerprintAsBitVect(query_molecule, 2)
    fps = [AllChem.GetMorganFingerprintAsBitVect(mol, 2) for mol in molecules]
    similarities = [DataStructs.TanimotoSimilarity(query_fp, fp) for fp in fps]
    smiles_similarity = list(zip(smiles_list, similarities))
    top3 = sorted(smiles_similarity, key=lambda x: x[1], reverse=True)[:3]
    return [x[0] for x in top3], [x[1] for x in top3]

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

def generate_reactions_by_similarity(smiles):
    file = '/home/zhujingyuan/chatbot/data/data_all_publish_info.csv'
    data = pd.read_csv(file)

    smiles_list = list(set(list(data['R1'])))

    smiles_top3, score_top3 = calculate_similarity(smiles, smiles_list)

    reactions_dict = {}

    reactions_dict[smiles] = {}

    r2_candidates = []
    for smiles_index, smiles_ref in enumerate(smiles_top3):
        sim_score = 'Similarity Score: {}'.format(str(round(score_top3[smiles_index],2)))
        reactions_dict[smiles][smiles_ref] = []
        reactions_dict[smiles][smiles_ref].append({'sim_score': sim_score,
                                     'conds_sum': [],
                            'yields': [],
                            'doi': [],
                            'rxn_origin': [],
                            'rxn_new': []})
        for i, row in data.iterrows():
            r1 = row['R1']
            r2 = row['R2']
            prd = row['Prd']
            lig_smiles = row['Add Lig SMILES']
            yields = row['Yield']
            doi = row['DOI']
            conds_sum = row['Cond Sum']
            conds_sum = format_conditions(conds_sum)
            yields= 'Yields: ' + str(yields) + '%'
            doi= 'DOI: ' + str(doi)

            if r1 == smiles_ref and type(r2) == str and '.' not in r2 and int(row['Yield']) > 80 and r2 not in r2_candidates:
                r2_candidates.append(r2)
                rxn_smiles = r1 + '.' + r2 + '>>' + prd

                rxn_smiles_mapped = get_rxnmapped_reaction(rxn_smiles)
                rxn = process_an_example(rxn_smiles_mapped)
                rxn = rxn.split('>>')[1] + '>>' + rxn.split('>>')[0]
                # rxn = '({})>>{}'.format(rxn.split('>>')[0], rxn.split('>>')[1])
                if rxn:
                    # rxn_new = reaction_outcome_prediction(smiles, r2)

                    reactions_dict[smiles][smiles_ref][0]['conds_sum'].append(conds_sum)
                    reactions_dict[smiles][smiles_ref][0]['yields'].append(yields)
                    reactions_dict[smiles][smiles_ref][0]['doi'].append(doi)

                    reactions_dict[smiles][smiles_ref][0]['rxn_origin'].append(rxn_smiles)

                    reactions_dict[smiles][smiles_ref][0]['rxn_new'].append(smiles + '.' + r2)

    return(reactions_dict)

def check_aromatic(smiles):
    mol = Chem.MolFromSmiles(smiles)
    mol = Chem.rdmolops.RemoveHs(mol)
    Chem.rdmolops.Kekulize(mol, clearAromaticFlags=True)
    Chem.rdmolops.SetAromaticity(mol)
    return Chem.MolToSmiles(mol)

def check_rxn(rxn_origin, reactants_smi, target_smiles):
    target_smiles = check_aromatic(target_smiles)

    reactant_origin_1 = rxn_origin.split('>>')[0].split('.')[0]
    reactant_origin_1 = check_aromatic(reactant_origin_1)
    reactant_origin_2 = rxn_origin.split('>>')[0].split('.')[1]
    reactant_origin_2 = check_aromatic(reactant_origin_2)

    reactant_new_1 = reactants_smi.split('.')[0]
    reactant_new_2 = reactants_smi.split('.')[1]

    if reactant_origin_1 == target_smiles:
        E_origin = reactant_origin_1
        Nu = reactant_origin_2
        rxn_origin = E_origin + '.' + Nu + '>>' + check_aromatic(rxn_origin.split('>>')[1])
        reactants_smi = E_origin + '.' + Nu 
        return rxn_origin, reactants_smi, Nu
    if reactant_origin_2 == target_smiles:
        E_origin = reactant_origin_2
        Nu = reactant_origin_1
        rxn_origin = E_origin + '.' + Nu + '>>' + check_aromatic(rxn_origin.split('>>')[1])
        reactants_smi = E_origin + '.' + Nu 
        return rxn_origin, reactants_smi, Nu

    if reactant_origin_1 != reactant_new_1  and reactant_origin_1 != reactant_new_2:
        E_origin = reactant_origin_1
        Nu = reactant_origin_2
        rxn_origin = E_origin + '.' + Nu + '>>' + check_aromatic(rxn_origin.split('>>')[1])
        if Nu == reactant_new_1:
            reactants_smi = reactant_new_2 + '.' + reactant_new_1
        else:
            reactants_smi = reactant_new_1 + '.' + reactant_new_2

    else:
        E_origin = reactant_origin_2
        Nu = reactant_origin_1
        rxn_origin = E_origin + '.' + Nu + '>>' + check_aromatic(rxn_origin.split('>>')[1])
        if Nu == reactant_new_1:
            reactants_smi = reactant_new_2 + '.' + reactant_new_1
        else:
            reactants_smi = reactant_new_1 + '.' + reactant_new_2

    return rxn_origin, reactants_smi, Nu

def correct_ligand(all_reactions_dict):
    error_ligand = {'PCy3鈥\ue52eBF4':'PCy3.HBF4', 'IPr(Ph)-OMe鈥\ue52eCl': 'IPr(Ph)-OMe.HCl', 'IPr鈥\ue52eCl' : 'IPr.HCl'}

    for target_smiles, ref_smiles_dict in all_reactions_dict.items():
        for ref_smiles, reaction_details in ref_smiles_dict.items():
            sim_score = reaction_details[0]['sim_score']
            for i in range(len(reaction_details[0]['conds_sum'])):
                conds_sum = reaction_details[0]['conds_sum'][i]
                for wrong, correct in error_ligand.items():
                    conds_sum = conds_sum.replace(wrong, correct)
                    all_reactions_dict[target_smiles][ref_smiles][0]['conds_sum'][i] = conds_sum

    return all_reactions_dict

def generate_product(smiles):
    all_reactions_dict = generate_reactions_by_similarity(smiles)
    all_reactions_dict = correct_ligand(all_reactions_dict)
    for target_smiles, ref_smiles_dict in all_reactions_dict.items():
        for ref_smiles, reaction_details in ref_smiles_dict.items():
            for i in range(len(reaction_details[0]['conds_sum'])):
                rxn_origin = reaction_details[0]['rxn_origin'][i]
                if len(rxn_origin) != 0:
                    rxn_new = reaction_details[0]['rxn_new'][i]
                    reactants_smi = rxn_new.split('>>')[0]
                    try:
                        rxn_origin, reactants_smi, Nu = check_rxn(rxn_origin, reactants_smi, target_smiles)
                        E_Main_smi = get_E_Main(target_smiles)
                        Nu_Main_smi = get_Nu_Main(rxn_origin, Nu)
                        product_smiles = connect_E_Nu(E_Main_smi, Nu_Main_smi)
                        reaction_details[0]['rxn_new'][i] = reactants_smi + '>>' + product_smiles
                        reaction_details[0]['rxn_origin'][i] = rxn_origin
                    except:
                        pass

    return all_reactions_dict


