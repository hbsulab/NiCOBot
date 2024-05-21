import re
from rdkit import Chem
from rdkit.Chem import AllChem
from rxnmapper import RXNMapper

def get_E_Main(smiles):
    mol = Chem.MolFromSmiles(smiles)

    Chem.Kekulize(mol, clearAromaticFlags=True)
    kekule_smiles = Chem.MolToSmiles(mol, kekuleSmiles=True)
    mol = Chem.MolFromSmiles(kekule_smiles)
    Chem.Kekulize(mol, clearAromaticFlags=True)

    for bond in mol.GetBonds():
        begin_atom = bond.GetBeginAtom()
        end_atom = bond.GetEndAtom()
        
        if ((begin_atom.GetSymbol() == 'C' and end_atom.GetSymbol() == 'O') or
            (begin_atom.GetSymbol() == 'O' and end_atom.GetSymbol() == 'C')) and \
        bond.GetBondType() == Chem.rdchem.BondType.SINGLE:
            
            if begin_atom.GetSymbol() == 'C':
                neighbors = begin_atom.GetNeighbors()
                neighbors = [ n.GetSymbol() for n in neighbors]
                if len(neighbors) != 1 and neighbors.count('O') == 1:
                    bond_to_break = (begin_atom.GetIdx(), end_atom.GetIdx())
                    if begin_atom.GetSymbol() == 'C':
                        O_connected_Idx = begin_atom.GetIdx()
                    elif end_atom.GetSymbol() == 'C':
                        O_connected_Idx = end_atom.GetIdx()
                    break
            
            if end_atom.GetSymbol() == 'C':
                neighbors = end_atom.GetNeighbors()
                neighbors = [ n.GetSymbol() for n in neighbors]
                if len(neighbors) != 1 and neighbors.count('O') == 1:
                    bond_to_break = (begin_atom.GetIdx(), end_atom.GetIdx())
                    if begin_atom.GetSymbol() == 'C':
                        O_connected_Idx = begin_atom.GetIdx()
                    elif end_atom.GetSymbol() == 'C':
                        O_connected_Idx = end_atom.GetIdx()
                    break

    virtual_atom_symbol = '[{}*]'.format(str(O_connected_Idx))
    
    fragments = Chem.FragmentOnBonds(mol, [mol.GetBondBetweenAtoms(*bond_to_break).GetIdx()], addDummies=True)

    fragments_smiles = Chem.MolToSmiles(fragments)

    fragments_smiles = fragments_smiles.split('.')
    for frag in fragments_smiles:
        frag_mol = Chem.MolFromSmiles(frag)
        for bond in frag_mol.GetBonds():
            begin_atom = bond.GetBeginAtom()
            end_atom = bond.GetEndAtom()
            
            if ((begin_atom.GetSymbol() == '*' and end_atom.GetSymbol() == 'C') or
                (begin_atom.GetSymbol() == 'C' and end_atom.GetSymbol() == '*')):
                
                E_frag = frag

    if virtual_atom_symbol in E_frag:
        escaped_virtual_atom_symbol = re.escape(virtual_atom_symbol)
        pattern = escaped_virtual_atom_symbol
        E_frag = re.sub(pattern,'',E_frag)
    
    return E_frag

def get_mapping_list(smi_mapped):
    mol = Chem.MolFromSmiles(smi_mapped)
    atoms = mol.GetAtoms()
    mapping_list = []
    for atom in atoms:
        try:
            mapping_list.append(atom.GetProp('molAtomMapNumber'))
        except:
            pass
    return mapping_list

def get_Nu_Main(rxn, Nu_smi):
    rxn_mapper = RXNMapper()
    results = rxn_mapper.get_attention_guided_atom_maps([rxn])
    smi = results[0]['mapped_rxn']

    reactants_smi = smi.split('>')[0]
    prod = smi.split('>')[-1]

    Nu = Chem.MolFromSmiles(Nu_smi)
    Nu_inchi = Chem.MolToInchi(Nu)
    Nu = Chem.MolFromSmiles(Nu_smi)
    Nu_inchi = Chem.MolToInchi(Nu)

    reactants = reactants_smi.split('.')
    reactants = [Chem.MolFromSmiles(r) for r in reactants]

    reactants_inchi = [Chem.MolToInchi(r) for r in reactants]

    Nu_index = [ i for i, r_inchi in enumerate(reactants_inchi) if r_inchi == Nu_inchi][0]

    if Nu_index == 0:
        E_index = 1
    else:
        E_index =  0

    E_smi_mapped = reactants_smi.split('.')[E_index]
    Nu_smi_mapped = reactants_smi.split('.')[Nu_index]

    E_atom_mapping_list = get_mapping_list(E_smi_mapped)
    Nu_atom_mapping_list = get_mapping_list(Nu_smi_mapped)

    mol = Chem.MolFromSmiles(prod)

    for bond in mol.GetBonds():
        begin_atom = bond.GetBeginAtom()
        end_atom = bond.GetEndAtom()
        
        if (begin_atom.GetProp('molAtomMapNumber') in E_atom_mapping_list and end_atom.GetProp('molAtomMapNumber') in Nu_atom_mapping_list)\
            or (begin_atom.GetProp('molAtomMapNumber') in Nu_atom_mapping_list and end_atom.GetProp('molAtomMapNumber') in E_atom_mapping_list):
            bond_to_break_dict = {begin_atom.GetIdx():begin_atom.GetProp('molAtomMapNumber'), end_atom.GetIdx():end_atom.GetProp('molAtomMapNumber')}
            break
    
    bond_to_break = tuple(bond_to_break_dict.keys())
    fragments = Chem.FragmentOnBonds(mol, [mol.GetBondBetweenAtoms(*bond_to_break).GetIdx()], addDummies=True)

    fragments_smiles = Chem.MolToSmiles(fragments)

    for k, v in bond_to_break_dict.items():
        if v in E_atom_mapping_list:
            Nu_RC_atomIdx = k
            break

    frag_1_smiles = fragments_smiles.split('.')[0]
    frag_2_smiles = fragments_smiles.split('.')[1]

    pattern = r'(?<!\d)\*(?!\])'
    frag_1_smiles = re.sub(pattern, '[0*]', frag_1_smiles)
    frag_2_smiles = re.sub(pattern, '[0*]', frag_2_smiles)

    pattern = r"\[(\d+)\*\]"

    matches1 = re.findall(pattern, frag_1_smiles)
    matches2 = re.findall(pattern, frag_2_smiles)

    matches1_int = [int(match) for match in matches1][0]
    matches2_int = [int(match) for match in matches2][0]

    if matches1_int == Nu_RC_atomIdx:
        Nu_frag = frag_1_smiles
    else:
        Nu_frag = frag_2_smiles
    
    return Nu_frag
    
def set_connected_label(smiles):
    pattern = r'\[\d+\*\]'
    substructure = re.findall(pattern, smiles)[0]

    mol = Chem.MolFromSmiles(smiles)
    for bond in mol.GetBonds():
        begin_atom = bond.GetBeginAtom()
        end_atom = bond.GetEndAtom()

        if begin_atom.GetSymbol() == '*':
            end_atom.SetProp('ReactionCenter', 'Yes')
        
        if end_atom.GetSymbol() == '*':
            begin_atom.SetProp('ReactionCenter', 'Yes')
    
    mol = AllChem.DeleteSubstructs(mol, Chem.MolFromSmarts(substructure))
    return mol

def get_connected_atomIdx(combined_mol):
    connected_list = []
    for atom in combined_mol.GetAtoms():
        try:
            if atom.GetProp('ReactionCenter'):
                connected_list.append(atom.GetIdx())
        except:
            pass
    return connected_list

def connect_E_Nu(E_Main_smi,Nu_Main_smi):
    mol1 = set_connected_label(E_Main_smi)
    mol2 = set_connected_label(Nu_Main_smi)

    combined_mol = Chem.CombineMols(mol1, mol2)

    editor = Chem.EditableMol(combined_mol)

    connected_list = get_connected_atomIdx(combined_mol)

    editor.AddBond(connected_list[0], connected_list[1], Chem.rdchem.BondType.SINGLE)

    # 获取编辑后的分子
    new_mol = editor.GetMol()

    # 清洁新分子的化学结构
    new_mol.UpdatePropertyCache()
    Chem.SanitizeMol(new_mol)

    # 将结果分子转换为 SMILES 字符串
    product_smiles = Chem.MolToSmiles(new_mol)

    return product_smiles