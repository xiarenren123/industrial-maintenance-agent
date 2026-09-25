from pathlib import Path
import re


# 设备名称到知识文件名的对应关系，集中写在这里便于以后维护。
KNOWLEDGE_FILES = {
    "三相异步电机": "motor.md",
    "PLC": "plc.md",
    "低压电气控制回路": "electrical.md",
}


def load_knowledge(equipment_type: str) -> str:
    """根据设备类型读取对应 Markdown 文件，并返回其中的文本。"""
    if equipment_type not in KNOWLEDGE_FILES:
        raise ValueError(f"暂时没有设备类型“{equipment_type}”的知识资料。")

    knowledge_path = Path(__file__).parent / "knowledge" / KNOWLEDGE_FILES[equipment_type]
    return knowledge_path.read_text(encoding="utf-8")


def chunk_knowledge(knowledge: str) -> list[str]:
    """按 Markdown 小节分块；没有小节标题时按自然段分块。"""
    text = knowledge.strip()
    if not text:
        return []

    # 二至六级标题作为边界，保留标题和它下面的完整内容。
    heading_pattern = r"(?m)(?=^#{2,6}[ \t]+)"
    if re.search(r"(?m)^#{2,6}[ \t]+", text):
        sections = re.split(heading_pattern, text)
        # 文档开头的总标题或介绍并入第一个小节，避免单独成为一个块。
        introduction = sections.pop(0).strip()
        chunks = [section.strip() for section in sections if section.strip()]
        if introduction:
            chunks[0] = introduction + "\n\n" + chunks[0]
        return chunks

    # 没有小节标题时，以空行为边界，不按字符数截断句子。
    paragraphs = re.split(r"\n\s*\n", text)
    return [paragraph.strip() for paragraph in paragraphs if paragraph.strip()]
