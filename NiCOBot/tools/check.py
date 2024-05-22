import pandas as pd

from langchain.tools import BaseTool

from NiCOBot.utils import *

class SimilarControlChemCheck(BaseTool):
    name = "SimilarityToControlChem"
    description = "Input SMILES, returns similarity to controlled chemicals."

    def _run(self, smiles: str) -> str:
        """Checks max similarity between compound and controlled chemicals.
        Input SMILES string."""

        data_path = 'NiCOBot/data/chem_wep_smi.csv'
        cw_df = pd.read_csv(data_path)

        try:
            if not is_smiles(smiles):
                return "Please input a valid SMILES string."

            max_sim = (
                cw_df["smiles"]
                .apply(lambda x: self.tanimoto(smiles, x))
                .max()
            )
            if max_sim > 0.35:
                return (
                    f"{smiles} has a high similarity "
                    f"({max_sim:.4}) to a known controlled chemical."
                )
            else:
                return (
                    f"{smiles} has a low similarity "
                    f"({max_sim:.4}) to a known controlled chemical."
                    "This is substance is safe, you may proceed with the task."
                )
        except:
            return "Tool error."

    def tanimoto(self, s1, s2):
        sim = tanimoto(s1,s2)
        if isinstance(sim, float):
            return sim
        return 0.0

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()

class ControlChemCheck(BaseTool):
    name = "ControlChemCheck"
    description = "Input CAS number, True if molecule is a controlled chemical."
    similar_control_chem_check = SimilarControlChemCheck()

    def _run(self, query: str) -> str:
        """Checks if compound is a controlled chemical. Input CAS number."""
        data_path = 'NiCOBot/data/chem_wep_smi.csv'
        cw_df = pd.read_csv(data_path)
        try:
            if is_smiles(query):
                query_esc = re.escape(query)
                found = (
                    cw_df["smiles"]
                    .astype(str)
                    .str.contains(f"^{query_esc}$", regex=True)
                    .any()
                )
            else:
                found = (
                    cw_df["cas"]
                    .astype(str)
                    .str.contains(f"^\({query}\)$", regex=True)
                    .any()
                )
            if found:
                return (
                    f"The molecule {query} appears in a list of "
                    "controlled chemicals."
                )
            else:
                # Get smiles of CAS number
                try:
                    smi = query2smiles(query)
                except ValueError as e:
                    return str(e)
                # Check similarity to known controlled chemicals
                return self.similar_control_chem_check._run(smi)

        except Exception as e:
            return f"Error: {e}"

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()

class Query2SMILES(BaseTool):
    name = "Name2SMILES"
    description = "Input a molecule name, returns SMILES."
    url: str = None
    ControlChemCheck = ControlChemCheck()

    def __init__(
        self,
    ):
        super().__init__()
        self.url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{}/{}"

    def _run(self, query: str) -> str:
        """This function queries the given molecule name and returns a SMILES string from the record"""
        """Useful to get the SMILES string of one molecule by searching the name of a molecule. Only query with one specific name."""
        try:
            smi = query2smiles(query, self.url)
        except ValueError as e:
            return str(e)
        # check if smiles is controlled
        msg = "Note: " + self.ControlChemCheck._run(smi)
        if "high similarity" in msg or "appears" in msg:
            return f"CAS number {smi}found, but " + msg
        return smi

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()

# need add this function
# class SMILES2CAS(BaseTool):
#     name = "SMILES2CAS"
#     description = "Input a SMILES, returns CAS number."
#     url: str = None
#     ControlChemCheck = ControlChemCheck()

#     def __init__(
#         self,
#     ):
#         super().__init__()
#         self.url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{}/{}"

#     def _run(self, query: str) -> str:
#         """This function queries the given molecule name and returns a SMILES string from the record"""
#         """Useful to get the SMILES string of one molecule by searching the name of a molecule. Only query with one specific name."""
#         try:
#             smi = query2smiles(query, self.url)
#         except ValueError as e:
#             return str(e)
#         # check if smiles is controlled
#         msg = "Note: " + self.ControlChemCheck._run(smi)
#         if "high similarity" in msg or "appears" in msg:
#             return f"CAS number {smi}found, but " + msg
#         return smi

#     async def _arun(self, query: str) -> str:
#         """Use the tool asynchronously."""
#         raise NotImplementedError()

class CheckEOrNu(BaseTool):
    name = "CheckEOrNu"
    description = "Input molecule SMILES, returns if it is an electrophile or nucleophile."

    def __init__(
        self,
        ):
        super().__init__()

    def _run(self, query: str) -> str:
        """Checks if molecule is an electrophile or nucleophile. Input molecule name."""
        try:
            if 'Mg' in query or 'B' in query or 'Zn' in query:
                return "This is a nucleophile."
            else:
                return "This is an electrophile."
        except:
            return "Tool error."

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()

class CheckCOBondStrength(BaseTool):
    name = "CheckCOBondStrength"
    description = "Input a electrophile SMILES and measure its C-O bond strength, returns if it has an inert, medium or weak C-O bond."

    def __init__(
        self,
        ):
        super().__init__()

    def _run(self, query: str) -> str:
        """Checks if molecule is an electrophile or nucleophile. Input molecule name."""
        try:
            try:
                mol = Chem.MolFromSmiles(query)
            except:
                return "Please input a valid SMILES string."
            subs = ['O=S(O)=O', 'O=PO', 'OC=O']
            check = 0
            for sub_smi in subs:
                sub_mol = Chem.MolFromSmiles(sub_smi)
                if mol.HasSubstructMatch(sub_mol):
                    check = 1
                    break
            if sub_smi == 'O=S(O)=O':
                return "This molecule has a weak C-O bond."
            elif sub_smi == 'O=PO':
                return "This molecule has a medium C-O bond."
            elif sub_smi == 'OC=O' and check == 1:
                return "This molecule has a medium C-O bond."
            elif check == 0:
                return "This molecule has an inert C-O bond."
        except:
            return "Tool error."

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()