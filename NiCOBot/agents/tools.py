import os

from langchain import agents
from langchain_experimental.tools import PythonREPLTool
from langchain.base_language import BaseLanguageModel

from NiCOBot.tools import *


def make_tools(llm: BaseLanguageModel, api_keys: dict = {}, verbose=True):
    serp_key = api_keys.get("SERP_API_KEY") or os.getenv("SERP_API_KEY")
    openai_api_key = api_keys.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")

    all_tools = agents.load_tools(
        [
            # "ddg-search",
            "wikipedia",
            # "human"
        ]
    )

    all_tools += [
        PythonREPLTool(),
        # ControlChemCheck(),
        Query2SMILES(),
        # Query2Reactions(),
        # Query2ReactionsEmbedding(),
        # Query2CSV(),
        # Query2Dataframe(),
        Query2ReactionSimilarity(),
        CheckEOrNu(),
        CheckCOBondStrength(),
        # PaperAnalysis(),
        Image2SMILES(),
        TableExtractor(),
        JSON2SMILES(),
    ]

    return all_tools
