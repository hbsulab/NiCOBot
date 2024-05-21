json_example = '''Here is the output example: [
                                {
                                "Title": ,
                                "Entries": [
                                {
                                "entry": 1,
                                "substrate 1": ,
                                "substrate 2": ,
                                "product": ,
                                "Ni catalyst": ,
                                "ligand": ,
                                "base": ,
                                "solvent": ,
                                "additive": ,
                                "temperature": ,
                                "time": ,
                                "yield": 
                                },
                                {
                                "entry": 2,
                                "substrate 1": ,
                                "substrate 2": ,
                                "product": ,
                                "Ni catalyst": ,
                                "ligand": ,
                                "base": ,
                                "solvent": ,
                                "additive": ,
                                "temperature": ,
                                "time": "",
                                "yield": 
                                },
                                {
                                "entry": 3,
                                "substrate 1": ,
                                "substrate 2": ,
                                "product": ,
                                "Ni catalyst": ,
                                "ligand": ,
                                "base": ,
                                "solvent": ,
                                "additive": ,
                                "temperature": ,
                                "time": "",
                                "yield": 
                                },
                                {
                                "entry": 4,
                                "substrate 1": ,
                                "substrate 2": ,
                                "product": ,
                                "Ni catalyst": ,
                                "ligand": ,
                                "base": ,
                                "solvent": ,
                                "additive": ,
                                "temperature": ,
                                "time": "",
                                "yield": 
                                },
                                {
                                "entry": 5,
                                "substrate 1": ,
                                "substrate 2": ,
                                "product": ,
                                "Ni catalyst": ,
                                "ligand": ,
                                "base": ,
                                "solvent": ,
                                "additive": ,
                                "temperature": ,
                                "time": "",
                                "yield": 
                                }
                                ]
                                }
                                ]'''

def get_table_format():
    return json_example

table_output = '''json
[
  {
    "Title": "Optimization of reaction conditions",
    "Entries": [
      {
        "entry": 1,
        "substrate 1": "1a",
        "substrate 2": "PhB(OH)2",
        "product": "N/A",
        "Ni catalyst": "[Ni(cod)2] (0.05mmol)",
        "ligand": "PCy3 (0.10mmol)",
        "base": "NaOH",
        "solvent": "dioxane",
        "additive": "N/A",
        "temperature": "80",
        "time": "12 hours",
        "yield": "0"
      },
      {
        "entry": 2,
        "substrate 1": "1a",
        "substrate 2": "PhBF3K",
        "product": "N/A",
        "Ni catalyst": "[Ni(cod)2] (0.05mmol)",
        "ligand": "PCy3 (0.10mmol)",
        "base": "NaOEt",
        "solvent": "dioxane",
        "additive": "N/A",
        "temperature": "80",
        "time": "12 hours",
        "yield": "0"
      },
      {
        "entry": 3,
        "substrate 1": "1a",
        "substrate 2": "NaBPh4",
        "product": "N/A",
        "Ni catalyst": "[Ni(cod)2] (0.05mmol)",
        "ligand": "PCy3 (0.10mmol)",
        "base": "NaOEt",
        "solvent": "dioxane",
        "additive": "N/A",
        "temperature": "80",
        "time": "12 hours",
        "yield": "8"
      },
      {
        "entry": 4,
        "substrate 1": "1a",
        "substrate 2": "2a",
        "product": "N/A",
        "Ni catalyst": "[Ni(cod)2] (0.05mmol)",
        "ligand": "PCy3 (0.10mmol)",
        "base": "NaOEt",
        "solvent": "dioxane",
        "additive": "N/A",
        "temperature": "80",
        "time": "12 hours",
        "yield": "64"
      },
      {
        "entry": 5,
        "substrate 1": "1a",
        "substrate 2": "2a",
        "product": "N/A",
        "Ni catalyst": "[Ni(cod)2] (0.05mmol)",
        "ligand": "PCy3 (0.10mmol)",
        "base": "CsF",
        "solvent": "dioxane",
        "additive": "N/A",
        "temperature": "80",
        "time": "12 hours",
        "yield": "54"
      },
      {
        "entry": 6,
        "substrate 1": "1a",
        "substrate 2": "2a",
        "product": "N/A",
        "Ni catalyst": "[Ni(cod)2] (0.05mmol)",
        "ligand": "PCy3 (0.20mmol)",
        "base": "CsF",
        "solvent": "dioxane",
        "additive": "N/A",
        "temperature": "80",
        "time": "12 hours",
        "yield": "47"
      },
      {
        "entry": 7,
        "substrate 1": "1a",
        "substrate 2": "2a",
        "product": "N/A",
        "Ni catalyst": "[Ni(cod)2] (0.05mmol)",
        "ligand": "PCy3 (0.20mmol)",
        "base": "CsF",
        "solvent": "toluene",
        "additive": "N/A",
        "temperature": "80",
        "time": "12 hours",
        "yield": "89"
      },
      {
        "entry": 8,
        "substrate 1": "1a",
        "substrate 2": "2a",
        "product": "N/A",
        "Ni catalyst": "[Ni(cod)2] (0.05mmol)",
        "ligand": "PCy3 (0.20mmol)",
        "base": "CsF",
        "solvent": "toluene",
        "additive": "N/A",
        "temperature": "120",
        "time": "12 hours",
        "yield": "93"
      }
    ]
  }
]
'''