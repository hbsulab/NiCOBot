import base64
import requests
import os
import re
import PyPDF2
from openai import OpenAI
from langchain.tools import BaseTool
from .table_format import get_table_format
from NiCOBot.utils import *


api_key = "XXXXXXXXXXXXXXXXX"

client = OpenAI(api_key=api_key)

# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

def generate_image_payload(base64_image, input):
    payload = {
    "model": "gpt-4-vision-preview",
    "temperature" : 0.1,
    "messages": [
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": input,
            },
            {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
            }
        ]
        }
    ],
    "max_tokens": 300
    }
   
    return payload

def extract_from_images(pdf_imagesdir, query):
    """Extracts text from images."""

    images = os.listdir(pdf_imagesdir)
    for image in images:
        image_path = os.path.join(pdf_imagesdir, image)
        base64_image = encode_image(image_path)

        headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
        }

        check_input = f"Does this image contain any table, figure, scheme information about {query}? You just need to answer 'yes' or 'no'."

        payload = generate_image_payload(base64_image, check_input)

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        check_answer = response.json()['choices'][0]['message']['content']

        if 'yes' in check_answer or 'Yes' in check_answer:
            extract_input = f"{query} in the image contains a chemical reaction equation. Please list the labels (for example, 1a, 2a....) of the reactants and products before and after the arrow in the chemical equation. Also, list the Nickel precatalyst, ligand, base, solvent, temperature, and time indicated above and below the arrow. Please do not make up answers."
            payload = generate_image_payload(base64_image, extract_input)
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            image_information = response.json()['choices'][0]['message']['content']
            return image_information
        else:
            continue

    return f"Can not find the {query} information in this paper. Please check your table or figure name."

def extract_from_text(query):

    # image_information = extract_from_images('pdf_output_images', query)
    image_information = '''Reactants:
                            Aryl methyl ether labeled as "1a"
                            Organoboron compound (not specifically labeled with a compound number)
                            Products:
                            Aryl boronate ester labeled as "2a"
                            The conditions listed above the arrow for the reaction are:
                            Nickel precatalyst: 10 mol% [Ni(cod)2]
                            Ligand: 20 mol% PCy3
                            Time: 12 hours'''

    pdf_dir = 'pdf_uploads'
    pdf_files = os.listdir(pdf_dir)

    pdf_file_path = os.path.join(pdf_dir, pdf_files[0])

    with open(pdf_file_path, 'rb') as pdf_content:
    # Create a PDF reader object
        pdf_reader = PyPDF2.PdfReader(pdf_content)
    # Iterate over all the pages in the PDF
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num] 
            page_text = page.extract_text()
            words = page_text.split() 
            page_text_join = ' '.join(words) 
            page_text_join = remove_ref(page_text_join)

            check_input = f"Do these contents contain any table, figure, scheme information about {query}? You just need to answer 'yes' or 'no'."

            message = check_input + '\n\n' + page_text_join
            messages = [
                {"role": "system", "content": "You answer questions about tables/schemes/figures caption in provided contents."},
                {"role": "user", "content": message},
            ]

            response = client.chat.completions.create(
            model='gpt-4-turbo-preview',
            messages=messages,
            temperature=0.1
            )
            check_answer = response.choices[0].message.content

            if 'yes' in check_answer or 'Yes' in check_answer:
                table_input = f'''I need you to read the table, its footnote and aditional context I provided and then return all entries information of {query} in JSON format.This JSON table should include the table title and the following columns: entry|substrate 1|substrate 2|product|Ni catalyst|ligand|base|solvent|additive|temperature|time|yield|.
                                  If a reagent in a cell has information about the equivalent in the text, the footnote or my previous prompts, please list it in the form of (equivalent) after this compound. If you can get the molecular SMILES, also list them. '''
                
                table_format = get_table_format()

                heading = f"This page contains content on the field of nickel-catalyzed C-O bond activation.\n\nAdditionol Context about this table:\n{image_information}\n\nContext:\n{page_text_join}\\nSMILES of 1a is COC1=CC2=CC=CC=C2C=C1\\n SMILES of 2a is CC1(C)COB(C2=CC=CC=C2)OC1\\n SMILES of product is C12=CC=CC=C1C=C(C3=CC=CC=C3)C=C2\n"

                message = heading + '\n\n' + table_input + '\n\n' + table_format

                messages = [
                    {"role": "system", "content": """Answer the question as truthfully as possible using the provided context,
                                                    and if the answer is not contained within the text below, say "N/A" """},
                    {"role": "user", "content": message},
                ]

                response = client.chat.completions.create(
                model='gpt-4-turbo-preview',
                messages=messages,
                temperature=0.1
                )
                table_information = response.choices[0].message.content

                return table_information
            else:
                continue

    return f"Can not find the {query} information in this paper. Please check your table or figure name."

class TableExtractor(BaseTool):
    name = "TableExtractor"
    description = "Input a table number and table name for example (Table 1: Optimization of reaction conditions.), extract reaction information from the table in the paper."

    def _run(self, query) -> str:
        """Extracts information from tables in PDFs."""
        table_information = extract_from_text(query)
        return table_information