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
from string import Template
from typing import List
from kag.interface import PromptABC
from knext.schema.client import SchemaClient
from knext.schema.model.base import SpgTypeEnum


# @PromptABC.register("default_ner")
@PromptABC.register("my_ner_prompt")
class OpenIENERPrompt(PromptABC):
    template_en = """
    {
    "instruction": "You're a very effective entity extraction system. Please extract all the entities that are important for knowledge build and question, along with type, category and a brief description. Return a JSON string.",
    "schema": $schema,
    "example": [
        {
            "input": "CHANGXING_1 Power Plant contains Unit 10...",
            "output": [
                        {
                            "name": "CHANGXING_1",
                            "type": "PowerPlant",
                            "category": "PowerPlant",
                            "description": "A power plant entity."
                        }
                    ]
        }
    ],
    "input": "$input"
}    
        """

    template_zh = """
    {
        "instruction": "你是工业领域命名实体识别的专家。请从输入中提取与模式定义匹配的实体。请注意：为了构建完善的知识图谱，不仅要提取物理设备（如电厂、机组、设备），还要提取关键的属性值（如KKS码、序列号、设备类型、单位），将它们也视为实体提取出来。请以JSON字符串格式返回。",
        "schema": $schema,
        "example": [
            {
                "input": "CHANGXING_1 电厂包含 10 号机组，10 号机组配置 HAD 主系统，HAD 主系统划分有 55 区域，55 区域部署设备 AA101，设备 AA101 的设备类型为 AA，序列号为 101；测点 SGC.CHANGXING_1.10HAD55AA101XQ11XQ12 位于CHANGXING_1 电厂的10 号机组的HAD 主系统的 55 区域，功能描述为中压汽包连排电动调节阀，测量值单位为 %。",
                "output": [
                            {
                                "name": "CHANGXING_1",
                                "category": "PowerPlant",
                                "description": "电厂名称"
                            },
                            {
                                "name": "10 号机组",
                                "category": "Unit",
                                "description": "机组编号"
                            },
                            {
                                "name": "HAD 主系统",
                                "category": "System",
                                "description": "主系统名称"
                            },
                            {
                                "name": "55 区域",
                                "category": "Area",
                                "description": "区域编号"
                            },
                            {
                                "name": "AA101",
                                "category": "Equipment",
                                "description": "设备名称"
                            },
                            {
                                "name": "AA",
                                "category": "Concept",
                                "description": "设备类型"
                            },
                            {
                                "name": "101",
                                "category": "Concept",
                                "description": "设备序列号"
                            },
                            {
                                "name": "SGC.CHANGXING_1.10HAD55AA101XQ11XQ12",
                                "category": "MeasurePoint",
                                "description": "名称"
                            },
                            {
                                "name": "10HAD55AA101XQ11XQ12",
                                "category": "Concept",
                                "description": "核心KKS码"
                            },
                            {
                                "name": "中压汽包连排电动调节阀",
                                "category": "Concept",
                                "description": "功能描述"
                            },
                            {
                                "name": "%",
                                "category": "Concept",
                                "description": "测量单位"
                            }
                        ]
            }
        ],
        "input": "$input"
    }    
        """

    def __init__(self, language: str = "", **kwargs):
        super().__init__(language, **kwargs)
        project_schema = SchemaClient(
            host_addr=self.kag_project_config.host_addr,
            project_id=self.kag_project_config.project_id,
        ).load()
        self.schema = []
        for name, value in project_schema.items():
            # filter out index types
            if value.spg_type_enum != SpgTypeEnum.Index:
                self.schema.append(name)

        self.template = Template(self.template).safe_substitute(
            schema=json.dumps(self.schema)
        )

    @property
    def template_variables(self) -> List[str]:
        return ["input"]

    def parse_response(self, response: str, **kwargs):
        rsp = response
        if isinstance(rsp, str):
            rsp = json.loads(rsp)
        if isinstance(rsp, dict) and "output" in rsp:
            rsp = rsp["output"]
        if isinstance(rsp, dict) and "named_entities" in rsp:
            entities = rsp["named_entities"]
        else:
            entities = rsp

        return entities