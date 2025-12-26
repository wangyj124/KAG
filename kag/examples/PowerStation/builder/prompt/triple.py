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


# @PromptABC.register("default_triple")
@PromptABC.register("my_triple_prompt")
class OpenIETriplePrompt(PromptABC):
    template_en = """
{
    "instruction": "You are an expert specializing in carrying out open information extraction (OpenIE)...",
    "entity_list": $entity_list,
    "input": "$input",
    "example": {
        "input": "...",
        "entity_list": [],
        "output": []
    }
}    
    """

    template_zh = """
{
    "instruction": "您是一位专门从事工业数据关系提取（OpenIE）的专家。请从 input 文本中提取关系三元组。规则如下：\n1. 提取结果必须为 [Subject, Predicate, Object] 格式。\n2. Subject 或 Object 中至少有一个必须出现在 entity_list 中。\n3. **重要**：如果文中描述一个实体同时位于多个层级（例如“测点A位于电厂B、机组C及区域D”），请务必将其拆解为多条独立的“位于”关系（[A, 位于, B], [A, 位于, C], [A, 位于, D]），不要遗漏。\n4. 关注层级关系（包含、配置、划分、位于）和属性关系（监测、设备类型为、核心KKS码为、功能描述为、单位为）。",
    "entity_list": $entity_list,
    "input": "$input",
    "example": {
        "input": "CHANGXING_1 电厂包含 10 号机组，10 号机组配置 HAD 主系统，HAD 主系统划分有 55 区域，55 区域部署设备 AA101，设备 AA101 的设备类型为 AA，序列号为 101；测点 SGC.CHANGXING_1.10HAD55AA101XQ11XQ12 位于CHANGXING_1 电厂的10 号机组的HAD 主系统的 55 区域，功能描述为中压汽包连排电动调节阀，测量值单位为 %。",
        "entity_list": [
            {"name": "CHANGXING_1", "category": "PowerPlant"},
            {"name": "10 号机组", "category": "Unit"},
            {"name": "HAD 主系统", "category": "System"},
            {"name": "55 区域", "category": "Area"},
            {"name": "AA101", "category": "Equipment"},
            {"name": "SGC.CHANGXING_1.10HAD55AA101XQ11XQ12", "category": "MeasurePoint"},
            {"name": "10HAD55AA101XQ11XQ12", "category": "Concept"},
            {"name": "%", "category": "Concept"}
        ],
        "output":[
            ["CHANGXING_1", "包含", "10 号机组"],
            ["10 号机组", "配置", "HAD 主系统"],
            ["HAD 主系统", "划分有", "55 区域"],
            ["AA101", "设备类型为", "AA"],
            ["AA101", "设备序列号为", "101"],
            ["55 区域", "部署", "AA101"],
            ["SGC.CHANGXING_1.10HAD55AA101XQ11XQ12", "位于", "CHANGXING_1"],
            ["SGC.CHANGXING_1.10HAD55AA101XQ11XQ12", "位于", "10 号机组"],
            ["SGC.CHANGXING_1.10HAD55AA101XQ11XQ12", "位于", "HAD 主系统"],
            ["SGC.CHANGXING_1.10HAD55AA101XQ11XQ12", "位于", "55 区域"],
            ["SGC.CHANGXING_1.10HAD55AA101XQ11XQ12", "监测", "AA101"],
            ["SGC.CHANGXING_1.10HAD55AA101XQ11XQ12", "核心KKS码为", "10HAD55AA101XQ11XQ12"],
            ["SGC.CHANGXING_1.10HAD55AA101XQ11XQ12", "测量值单位为", "%"]
        ]
    }
}    
    """

    @property
    def template_variables(self) -> List[str]:
        return ["entity_list", "input"]

    def parse_response(self, response: str, **kwargs):
        rsp = response
        if isinstance(rsp, str):
            rsp = json.loads(rsp)
        if isinstance(rsp, dict) and "output" in rsp:
            rsp = rsp["output"]
        if isinstance(rsp, dict) and "triples" in rsp:
            triples = rsp["triples"]
        else:
            triples = rsp

        standardized_triples = []
        for triple in triples:
            if isinstance(triple, list):
                standardized_triples.append(triple)
            elif isinstance(triple, dict):
                s = triple.get("subject")
                p = triple.get("predicate")
                o = triple.get("object")
                if s and p and o:
                    standardized_triples.append([s, p, o])

        return standardized_triples
