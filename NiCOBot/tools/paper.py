import ast 
import re
from openai import OpenAI 
import pandas as pd  
import tiktoken  
from scipy import spatial 
from langchain.tools import BaseTool

# search function
def strings_ranked_by_relatedness(
    query: str,
    df: pd.DataFrame,
    relatedness_fn=lambda x, y: 1 - spatial.distance.cosine(x, y),
    client: OpenAI = None,
    top_n: int = 3
) -> tuple[list[str], list[float]]:
    """Returns a list of strings and relatednesses, sorted from most related to least."""
    query_embedding_response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=query,
    )
    query_embedding = query_embedding_response.data[0].embedding
    strings_and_relatednesses = [
        (row["content"], relatedness_fn(query_embedding, row["embedding"]))
        for i, row in df.iterrows()
    ]
    strings_and_relatednesses.sort(key=lambda x: x[1], reverse=True)
    strings, relatednesses = zip(*strings_and_relatednesses)
    return strings[:top_n], relatednesses[:top_n]

def num_tokens(text: str, model: str = None) -> int:
    """Return the number of tokens in a string."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))


def query_message(
    query: str,
    df: pd.DataFrame,
    model: str,
    token_budget: int,
    client: OpenAI = None
) -> str:
    """Return a message for GPT, with relevant source texts pulled from a dataframe."""
    strings, relatednesses = strings_ranked_by_relatedness(query, df, client=client)
    introduction = 'Use the below the Nickel Catalyzed C-O Bond Activation paper to answer the subsequent question. If the answer cannot be found in the reaction description, write "I could not find an answer."'
    question = f"\n\nQuestion: {query}"
    message = introduction
    for string in strings:
        next_article = f'"""\n{string}\n"""'
        if (
            num_tokens(message + next_article + question, model=model)
            > token_budget
        ):
            break
        else:
            message += next_article
    return message + question

def ask(
    query: str,
    df: pd.DataFrame = None,
    model: str = None,
    token_budget: int = 4096 - 500,
    print_message: bool = False,
    client: OpenAI = None
) -> str:
    """Answers a query using GPT and a dataframe of relevant texts and embeddings."""
    message = query_message(query, df, model=model, token_budget=token_budget, client=client)
    if print_message:
        print(message)
    messages = [
        {"role": "system", "content": "You answer questions about the Nickel Catalyzed C-O Bond Activation paper."},
        {"role": "user", "content": message},
    ]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.8
    )
    response_message = response.choices[0].message.content
    return response_message

class PaperAnalysis(BaseTool):
    name = "PaperAnalysis"
    description = "Input query, returns analysis of the paper."
    data: pd.DataFrame = None
    client: OpenAI = None

    def __init__(self):
        super().__init__()
        self.data = pd.read_csv('Papers_remove_review_embedding_DOI_Year.csv')
        self.client = OpenAI()

    def _run(self, query) -> str:
        """Analyzes a paper."""
        try:
            doi_pattern = r'10\.\d{4,9}/[-._;()/:A-Za-z0-9]+'
            matches = re.findall(doi_pattern, query)

            if len(matches) == 0:
                return "No DOI found in the query."
            else:
                doi = matches[0]

                paper_info = self.data.loc[
                    (self.data['DOI'] == doi),
                    ['content', 'embedding', 'Year']
                ]

                if paper_info.empty:
                    return f"No paper found for the given DOI {doi}."

                paper_info['embedding'] = paper_info['embedding'].apply(ast.literal_eval)

                print(paper_info)

                response = ask('These contents are from this paper. Can you summarize something?', client=self.client, df=paper_info, model="gpt-4-turbo-preview")
                return response
        except Exception as e:
            return str(e)

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()