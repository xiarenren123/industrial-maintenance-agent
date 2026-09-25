import json

from llm_client import ask_model


def evaluate_fault_relevance(equipment_type: str, fault_description: str) -> dict:
    """判断输入是否在描述所选设备的故障、异常或运行问题。"""
    prompt = f"""你是工业设备维护辅助分析助手。
判断用户描述是否与所选工业设备的故障、异常现象、运行问题或维护问题有关。
与设备无关的百科、学习、生活或其他主题应返回 false。
只能返回合法 JSON，不要 Markdown 或其他文字：{{"relevant": true}} 或 {{"relevant": false}}。

设备类型：{equipment_type}
用户描述：{fault_description}
"""
    try:
        result = ask_model(prompt)
        cleaned = result.strip().removeprefix("```json").removesuffix("```").strip()
        data = json.loads(cleaned)
        relevant = data.get("relevant")
        if not isinstance(relevant, bool):
            raise ValueError("relevant 不是布尔值")
        return {"relevant": relevant}
    except Exception:
        # 判断服务异常时继续原有流程，不因格式问题破坏已有功能。
        return {"relevant": True}


def evaluate_fault_information(equipment_type: str, fault_description: str) -> dict:
    """判断故障描述是否足够；异常时默认继续正常分析。"""
    prompt = f"""你是工业设备维护辅助分析助手。
请判断下面的故障描述是否已经具备进行初步分析的基本信息。
如果信息不足，只提出一个最有价值、普通操作人员可以回答的问题。
不要要求带电测试、拆线、拆机等危险操作。
你只能返回合法 JSON，不要 Markdown 代码块或其他文字，格式必须是：
{{"sufficient": true, "question": ""}}
或：
{{"sufficient": false, "question": "一个简单明确的问题"}}

设备类型：{equipment_type}
故障描述：{fault_description}
"""
    try:
        result = ask_model(prompt)
        # 兼容模型偶尔加上的 ```json ... ``` 包裹。
        cleaned = result.strip().removeprefix("```json").removesuffix("```").strip()
        data = json.loads(cleaned)
        sufficient = data.get("sufficient")
        question = data.get("question", "")
        if not isinstance(sufficient, bool):
            raise ValueError("sufficient 不是布尔值")
        if not isinstance(question, str):
            question = ""
        return {"sufficient": sufficient, "question": question}
    except Exception:
        return {"sufficient": True, "question": ""}
