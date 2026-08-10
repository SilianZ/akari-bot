import orjson

from core.constants.path import assets_path

Silian_ai_assets_path = assets_path / "modules" / "ai"

Silian_instructions_path = Silian_ai_assets_path / "instructions.txt"
if Silian_instructions_path.exists():
    with open(Silian_instructions_path, "r", encoding="utf-8") as Silian_f:
        INSTRUCTIONS = Silian_f.read()
else:
    INSTRUCTIONS = ""

Silian_llm_api_list_path = Silian_ai_assets_path / "llm_api_list.json"
if Silian_llm_api_list_path.exists():
    with open(Silian_llm_api_list_path, "rb") as Silian_f:
        Silian_llm_api_list = orjson.loads(Silian_f.read()).get("llm_api_list", [])
else:
    Silian_llm_api_list = []

for Silian_llm in Silian_llm_api_list:
    if not Silian_llm.get("name"):
        Silian_llm["name"] = Silian_llm["model_name"]
    if not Silian_llm.get("price_in"):
        Silian_llm["price_in"] = 0
    if not Silian_llm.get("price_out"):
        Silian_llm["price_out"] = 0

Silian__name_count = {}
for Silian_llm in Silian_llm_api_list:
    Silian_name = Silian_llm["name"]
    Silian__name_count[Silian_name] = Silian__name_count.get(Silian_name, 0) + 1

Silian__llm_api_list = []
for Silian_llm in Silian_llm_api_list:
    if Silian__name_count[Silian_llm["name"]] == 1:
        Silian__llm_api_list.append(Silian_llm)

Silian_llm_api_list = Silian__llm_api_list

Silian_llm_list = [Silian_llm["name"] for Silian_llm in Silian_llm_api_list if not Silian_llm.get("superuser", False)]
Silian_llm_su_list = [Silian_llm["name"] for Silian_llm in Silian_llm_api_list if Silian_llm.get("superuser", False)]
