from llm_client import ask_model


def diagnose(
    equipment_type: str,
    fault_description: str,
    relevant_chunks: list[tuple[str, float]],
    similar_records: list[tuple[dict, float]] | None = None,
) -> str:
    """使用检索到的 Chunk 组织 Prompt，并调用模型生成辅助分析。"""
    # 只取 Chunk 文字；相似度分数用于页面调试，不需要发送给模型。
    reference_knowledge = "\n\n---\n\n".join(
        chunk for chunk, _score in relevant_chunks
    )
    if not reference_knowledge:
        reference_knowledge = (
            "未检索到达到相关度阈值的本地知识。只能给出一般性的辅助分析，"
            "不能把一般性推测当作本地资料结论。"
        )
    history_text = "\n\n---\n\n".join(
        f"历史故障描述：{record.get('fault_description', '')}\n"
        f"当时分析结果：{record.get('analysis_result', '')}\n"
        f"状态：{record.get('status', '待处理')}\n"
        f"时间：{record.get('created_at', '')}"
        for record, _score in (similar_records or [])
    ) or "没有检索到相关历史维护案例。"

    prompt = f"""你是一个“工业设备维护辅助分析助手”，不是实际维修人员。

请区分以下信息：

【用户故障描述】
这是用户对现场现象的描述。

【检索得到的参考知识】
这是根据用户描述从本地设备维护资料中检索出的辅助资料。请优先依据这些参考知识分析。若没有检索到资料，则说明本地知识库参考不足，只能给出一般性的辅助分析，并提醒需要进一步确认现场信息。

【相似历史维护案例】
历史案例只能作为辅助参考。即使案例相似，也不能直接认定当前故障原因与历史案例相同；必须结合当前故障描述和本地维护知识重新判断。

【分析要求】
如果参考知识不足以确定故障，不要编造唯一结论，必须说明“信息不足，需要进一步检查”，并指出还需要哪些信息。

涉及电气设备时，不要指导无资质人员进行带电拆接、带电测量等危险操作；优先提醒停机、断电、验电和防止误送电，并遵守现场安全规范。

请严格使用以下结构回答：

【故障现象】
简要整理用户输入

【可能原因】
列出 3～5 个可能原因，不要直接认定唯一故障

【建议排查顺序】
按照从简单、常见、低风险到进一步检查的顺序列出步骤

【安全注意事项】
给出必要的设备/电气安全提醒

【初步结论】
总结目前最值得优先检查的方向；信息不足时明确说明

设备类型：{equipment_type}

用户故障现象：
{fault_description}

检索得到的参考知识：
{reference_knowledge}

相似历史维护案例：
{history_text}
"""
    return ask_model(prompt)
