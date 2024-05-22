import ast
import pandas as pd
import os
from scipy import spatial

from langchain.tools import BaseTool
from langchain_openai import OpenAIEmbeddings
from langchain.agents.agent_types import AgentType
from langchain_experimental.agents import create_csv_agent
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain_openai import ChatOpenAI

from NiCOBot.utils import *
from NiCOBot.tools.check import ControlChemCheck

class Query2Reactions(BaseTool):
    name = "Query2Reactions"
    description = "Input a molecule name, returns the reaction description."
    data: pd.DataFrame = None
    ControlChemCheck = ControlChemCheck()

    def __init__(self):
        super().__init__()
        self.data = pd.read_csv('data/data_all_publish_info_with_descriptions_json_and_embeddings.csv')

    def _run(self, name: str) -> str:
        """This function queries the local CSV file with the given molecule name and SMILES and returns a reaction description."""
        try:
            reaction_info = self.data.loc[
                (self.data['E_IUPACName'] == name),
                'Description_Text'
            ]
            if reaction_info.empty:
                return f"No reaction found for the given name {name}."
            description = reaction_info.iloc[0]
            # Check if the description is about a controlled substance
            # msg = "Note: " + self.ControlChemCheck._run(smiles)
            # if "high similarity" in msg or "appears" in msg:
            #     return f"Description {description} found, but " + msg
            return description
        except Exception as e:
            return str(e)

    async def _arun(self, name: str, smiles: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()

class Query2ReactionsEmbedding(BaseTool):
    name = "Query2ReactionsEmbedding"
    description = "Input a query string, returns top N related reaction descriptions with their relatedness scores."
    data: pd.DataFrame = None
    client: OpenAIEmbeddings = None
    top_n: int = None
    
    def __init__(self, top_n: int = 3):
        super().__init__()
        self.data = pd.read_csv('data/data_all_publish_info_with_descriptions_json_and_embeddings.csv')
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAIEmbeddings(model="text-embedding-ada-002", openai_api_key=self.openai_api_key)
        self.top_n = top_n

    @staticmethod
    def relatedness_fn(x, y):
        return 1 - spatial.distance.cosine(x, y)

    def get_query_embedding(self, query: str):
        query_embedding = self.client.embed_query(query)
        return query_embedding

    def _run(self, query: str) -> tuple[list[str], list[float]]:
        """This function queries the local CSV file with the given query string and returns the top N related reaction descriptions with their relatedness scores."""
        try:
            query_embedding = self.get_query_embedding(query)
            strings_and_relatednesses = [
                (row['Description_Text'], self.relatedness_fn(query_embedding, ast.literal_eval(row['embedding'])))
                for _, row in self.data.iterrows()
            ]

            # Sort by relatedness scores in descending order
            strings_and_relatednesses.sort(key=lambda x: x[1], reverse=True)

            # Unzip the list of tuples into two lists
            strings, relatednesses = zip(*strings_and_relatednesses)

            # Return the top_n strings and their relatedness scores
            return list(strings[:self.top_n]), list(relatednesses[:self.top_n])
        except Exception as e:
            return str(e), []

    async def _arun(self, query: str) -> tuple[list[str], list[float]]:
        """Use the tool asynchronously."""
        raise NotImplementedError()

class Query2CSV(BaseTool):
    name = "Query2CSV"
    description = "Retrieve relevant Nickel catalyzed C-O bond activation reaction information from a CSV which including Nickel catalyzed C-O bond activation reaction details based on a query."
    data_path: str = None
    client: ChatOpenAI = None

    def __init__(self):
        super().__init__()
        self.data_path = 'data/data_all_publish_info_with_iupac_names.csv'
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.client = create_csv_agent(ChatOpenAI(temperature=0, 
                                                  model="gpt-4-0613", 
                                                  openai_api_key=self.openai_api_key),
                                                  self.data_path, 
                                                  verbose=True,
                                                  handle_parsing_errors=True)
    
    def _run(self, query: str) -> str:
        """This function queries the local CSV file with the given query string and returns the relevant information."""
        try:
            response = self.client.invoke(input=query)
            return response
        except Exception as e:
            return str(e)
    
    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()

class Query2Dataframe(BaseTool):
    name = "Query2Dataframe"
    description = "Retrieve relevant Nickel catalyzed C-O bond activation reaction information from a dataframe which including Nickel catalyzed C-O bond activation reaction details based on a query."
    df: pd.DataFrame = None
    client: ChatOpenAI = None

    def __init__(self):
        super().__init__()
        self.df = pd.read_csv('data/data_all_publish_info_with_iupac_names_C-O_strength.csv')
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.client = create_pandas_dataframe_agent(ChatOpenAI( temperature=0.1, 
                                                                model="gpt-4-0125-preview", 
                                                                openai_api_key=self.openai_api_key),
                                                                self.df, 
                                                                verbose=True,
                                                                handle_parsing_errors=True,
                                                                agent_type=AgentType.OPENAI_FUNCTIONS)
    
    def _run(self, query: str) -> str:
        """This function queries the local CSV file with the given query string and returns the relevant information."""
        try:
            response = self.client.invoke(input=query)
            return response
        except Exception as e:
            return str(e)
    
    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()