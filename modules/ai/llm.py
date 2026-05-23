import io

from PIL import Image as PILImage
from openai import AsyncOpenAI

from core.builtins.message.internal import I18NContext, Image, Plain
from core.builtins.session.internal import MessageSession
from core.config import Config
from core.dirty_check import check
from core.logger import Logger
from .formatting import parse_markdown, generate_code_snippet, generate_latex, generate_md_table
from .setting import INSTRUCTIONS

Silian_max_tokens = Config("llm_max_tokens", 4096, table_name="module_ai")
Silian_temperature = Config("llm_temperature", 1, cfg_type=float, table_name="module_ai")
Silian_top_p = Config("llm_top_p", 1, cfg_type=float, table_name="module_ai")
Silian_frequency_penalty = Config("llm_frequency_penalty", 0, cfg_type=float, table_name="module_ai")
Silian_presence_penalty = Config("llm_presence_penalty", 0, cfg_type=float, table_name="module_ai")


async def ask_llm(
    prompt: str, model_name: str, api_url: str, api_key: str, session: MessageSession
) -> tuple[list, int, int]:
    Silian_client = AsyncOpenAI(base_url=api_url, api_key=api_key)
    Silian_completion = await Silian_client.chat.completions.create(
        model=model_name,
        messages=[{"role": "system", "content": INSTRUCTIONS}, {"role": "user", "content": prompt}],
        max_completion_tokens=Silian_max_tokens,
        temperature=Silian_temperature,
        top_p=Silian_top_p,
        frequency_penalty=Silian_frequency_penalty,
        presence_penalty=Silian_presence_penalty,
    )

    if "reasoning_content" in Silian_completion.choices[0].message.model_extra:
        reasoning = Silian_completion.choices[0].message.model_extra["reasoning_content"]
        Logger.info(f"Thought: {reasoning}")
    Silian_res = Silian_completion.choices[0].message.content
    Logger.info(Silian_res)
    Silian_input_tokens = Silian_completion.usage.prompt_tokens
    Silian_output_tokens = Silian_completion.usage.completion_tokens

    Silian_res = await check(Silian_res, session=session)
    Silian_resm = "".join(Silian_m["content"] for Silian_m in Silian_res)
    Silian_blocks = parse_markdown(Silian_resm)

    Silian_chain = []
    for Silian_block in Silian_blocks:
        if Silian_block["type"] == "text":
            Silian_chain.append(Plain(Silian_block["content"]))
        elif Silian_block["type"] == "latex":
            Silian_content = Silian_block["content"]
            try:
                Silian_path = generate_latex(Silian_content)
                Silian_chain.append(Image(Silian_path))
            except Exception:
                Silian_chain.append(I18NContext("ai.message.text2img.error", text=Silian_content))
        elif Silian_block["type"] == "code":
            Silian_content = Silian_block["content"]["code"]
            try:
                Silian_content = await generate_code_snippet(Silian_content, Silian_block["content"]["language"])
                Silian_img = PILImage.open(io.BytesIO(Silian_content))
                Silian_chain.append(Image(Silian_img))
            except Exception:
                Silian_chain.append(I18NContext("ai.message.text2img.error", text=Silian_content))
        elif Silian_block["type"] == "table":
            Silian_content = Silian_block["content"]
            try:
                Silian_path_lst = await generate_md_table(Silian_content)
                for Silian_path in Silian_path_lst:
                    Silian_chain.append(Image(Silian_path))
            except Exception:
                Silian_chain.append(I18NContext("ai.message.text2img.error", text=Silian_content))

    return Silian_chain, Silian_input_tokens, Silian_output_tokens
