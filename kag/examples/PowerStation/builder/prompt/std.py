# -*- coding: utf-8 -*-
# Copyright 2023 OpenSPG Authors
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License
# is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
# or implied.

import json
from typing import List

from kag.interface import PromptABC


# @PromptABC.register("default_std")
@PromptABC.register("my_std_prompt")
class OpenIEEntitystandardizationdPrompt(PromptABC):
    template_en = """
{
    "instruction": "The `input` field contains a user provided context. The `named_entities` field contains extracted named entities...",
    "example": {
        "input": "...",
        "named_entities": [],
        "output": []
    },
    "input": "$input",
    "named_entities": $named_entities
}
    """

    template_zh = """
{
    "instruction": "input字段包含用户提供的上下文。命名实体字段包含从上下文中提取的命名实体。请对实体名称进行标准化：1. 去除冗余修饰词；2. 统一术语（如将别名转换为全称）；3. 如果实体名称本身已经很标准，请保持原样（official_name与name一致）。请返回包含 standardized entity 的 JSON 列表。",
    "example": {
        "input": "10 号机组配置 HAD 主系统，测点 SGC... 描述为中压汽包连排电动调节阀。",
        "named_entities": [
            {"name": "10 号机组", "category": "Unit"},
            {"name": "HAD 主系统", "category": "System"},
            {"name": "中压汽包连排电动调节阀", "category": "Concept"}
        ],
        "output": [
            {"name": "10 号机组", "category": "Unit", "official_name": "10号机组"},
            {"name": "HAD 主系统", "category": "System", "official_name": "HAD系统"},
            {"name": "中压汽包连排电动调节阀", "category": "Concept", "official_name": "中压汽包连排电动调节阀"}
        ]
    },
    "input": $input,
    "named_entities": $named_entities,
}    
    """

    @property
    def template_variables(self) -> List[str]:
        return ["input", "named_entities"]

    def parse_response(self, response: str, **kwargs):
        rsp = response
        if isinstance(rsp, str):
            rsp = json.loads(rsp)
        if isinstance(rsp, dict) and "output" in rsp:
            rsp = rsp["output"]
        if isinstance(rsp, dict) and "named_entities" in rsp:
            standardized_entity = rsp["named_entities"]
        else:
            standardized_entity = rsp
        entities_with_offical_name = set()
        merged = []
        entities = kwargs.get("named_entities", [])

        # The caller does not have a unified input data structure
        if "entities" in entities:
            entities = entities["entities"]
        if isinstance(entities, dict):
            _entities = []
            for category in entities:
                _e = entities[category]
                if isinstance(_e, list):
                    for _e2 in _e:
                        _entities.append({"name": _e2, "category": category})
                elif isinstance(_e, str):
                    _entities.append({"name": _e, "category": category})
                else:
                    pass

        for entity in standardized_entity:
            merged.append(entity)
            entities_with_offical_name.add(entity["name"])
        # in case llm ignores some entities
        for entity in entities:
            # Ignore entities without a name attribute
            if "name" in entity and entity["name"] not in entities_with_offical_name:
                entity["official_name"] = entity["name"]
                merged.append(entity)
        return merged
