from typing import Optional

import langchain
import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from pydantic import ValidationError
from rmrkl import ChatZeroShotAgent, RetryAgentExecutor

from .prompts import FORMAT_INSTRUCTIONS, QUESTION_PROMPT, REPHRASE_TEMPLATE, SUFFIX
from .tools import make_tools

def _make_llm(model, temp, api_key, streaming: bool = False):
    if model.startswith("gpt-3.5-turbo") or model.startswith("gpt-4"):
        llm = ChatOpenAI(
            temperature=temp,
            model_name=model,
            request_timeout=1000,
            streaming=streaming,
            callbacks=[StreamingStdOutCallbackHandler()],
            openai_api_key=api_key,
            # openai_api_base=os.getenv("OPENAI_API_BASE"),
        )
    elif model.startswith("text-"):
        llm = langchain.llms.OpenAI(
            temperature=temp,
            model_name=model,
            streaming=streaming,
            callbacks=[StreamingStdOutCallbackHandler()],
            openai_api_key=api_key,
        )
    else:
        raise ValueError(f"Invalid model name: {model}")
    return llm


class NiCOBot:
    def __init__(
        self,
        tools=None,
        model="gpt-4-turbo",
        tools_model="gpt-4-turbo",
        temp=0.1,
        max_iterations=40,
        verbose=True,
        memory=None,
        streaming: bool = True,
        openai_api_key: Optional[str] = None,
        api_keys: dict = {},
    ):

        load_dotenv()
        try:
            self.llm = _make_llm(model, temp, openai_api_key, streaming)
        except ValidationError:
            raise ValueError("Invalid OpenAI API key")

        if tools is None:
            api_keys["OPENAI_API_KEY"] = openai_api_key
            tools_llm = _make_llm(tools_model, temp, openai_api_key, streaming)
            tools = make_tools(tools_llm, api_keys=api_keys, verbose=verbose)

        # Initialize agent
        self.agent_executor = RetryAgentExecutor.from_agent_and_tools(
            tools=tools,
            agent=ChatZeroShotAgent.from_llm_and_tools(
                self.llm,
                tools,
                suffix=SUFFIX,
                format_instructions=FORMAT_INSTRUCTIONS,
                question_prompt=QUESTION_PROMPT,
            ),
            verbose=True,
            max_iterations=max_iterations,
            handle_parsing_errors=True,
            memory=memory,
        )

        rephrase = PromptTemplate(
            input_variables=["question", "chat_history", "agent_ans"], template=REPHRASE_TEMPLATE
        )

        self.rephrase_chain = LLMChain(prompt=rephrase, llm=self.llm)

    def invoke(self, prompt):
        outputs = self.agent_executor({"input": prompt})
        return outputs["output"]