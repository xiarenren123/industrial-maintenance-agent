import streamlit as st

from agent import evaluate_fault_information, evaluate_fault_relevance
from diagnosis import diagnose
from knowledge_loader import load_knowledge, chunk_knowledge
from retriever import retrieve_relevant_chunks
from maintenance_record import load_maintenance_records, save_maintenance_record
from history_retriever import retrieve_similar_records

st.set_page_config(page_title="工业设备智能运维助手", page_icon="⚙️", layout="wide")

# 限制宽屏内容宽度，保持阅读留白；其余布局使用 Streamlit 原生组件。
st.markdown("""
<style>
.stMainBlockContainer { max-width: 1120px; padding-top: 2rem; padding-bottom: 3rem; }
h1 { letter-spacing: -0.02em; }
</style>
""", unsafe_allow_html=True)

# session_state 用于在 Streamlit 重新运行后保留一次追问的上下文。
_DEFAULTS = {
    "analysis_result": "",
    "analysis_equipment_type": "",
    "analysis_fault_description": "",
    "original_fault_description": "",
    "agent_question": "",
    "supplemental_information": "",
    "waiting_for_supplement": False,
    "analysis_started_with_supplement": False,
    "debug_knowledge": "",
    "debug_chunks": [],
    "debug_relevant_chunks": [],
    "debug_similar_records": [],
}
for key, value in _DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


def run_rag_analysis(equipment_type: str, fault_description: str):
    """执行现有的读取、分块、检索和诊断流程。"""
    knowledge_text = load_knowledge(equipment_type)
    chunks = chunk_knowledge(knowledge_text)
    relevant_chunks = retrieve_relevant_chunks(
        fault_description, chunks, top_k=2, min_score=0.05
    )
    similar_records = retrieve_similar_records(equipment_type, fault_description, top_k=2, min_score=0.05)
    result = diagnose(equipment_type, fault_description, relevant_chunks, similar_records)
    return knowledge_text, chunks, relevant_chunks, similar_records, result


def show_debug_information(knowledge_text, chunks, relevant_chunks, similar_records):
    """把知识、Chunk 和检索结果放在统一的调试区域。"""
    with st.expander("开发调试信息", expanded=False):
        st.markdown("#### 原始知识内容")
        st.markdown(knowledge_text)
        st.markdown(f"#### 知识库分块结果（共 {len(chunks)} 个）")
        for index, chunk in enumerate(chunks, start=1):
            st.subheader(f"Chunk {index}")
            st.text(chunk)
        st.markdown("#### 知识检索结果")
        if not relevant_chunks:
            st.info("未检索到高相关度本地知识")
        for index, (chunk, score) in enumerate(relevant_chunks, start=1):
            st.subheader(f"检索结果 {index}")
            st.write(f"相似度：{score:.2f}")
            st.text(chunk)
        st.markdown("#### 查看相似历史案例")
        if not similar_records:
            st.info("未检索到相关历史维护案例")
        for index, (record, score) in enumerate(similar_records, start=1):
            st.write(f"案例 {index}｜相似度：{score:.2f}")
            st.write(f"创建时间：{record.get('created_at', '')}")
            st.write(f"设备类型：{record.get('equipment_type', '')}")
            st.write(f"历史故障描述：{record.get('fault_description', '')}")
            st.write(f"状态：{record.get('status', '待处理')}")
            st.caption("历史分析结果（仅供参考）")
            st.markdown(record.get("analysis_result", ""))
            st.divider()


st.sidebar.title("运维工作台")
page = st.sidebar.radio("页面", ["故障辅助分析", "历史维护记录"])

st.sidebar.divider()
st.sidebar.subheader("系统能力")
st.sidebar.markdown("✓ 本地维护知识库  \n✓ RAG相关知识检索  \n✓ 历史故障案例参考  \n✓ AI故障辅助分析")

if page == "历史维护记录":
    st.title("历史维护记录")
    records = load_maintenance_records()
    st.caption(f"累计记录：{len(records)} 条 · 按创建时间从新到旧排列")
    if not records:
        st.info("暂无维护记录")
    else:
        records.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        for record in records:
            with st.container(border=True):
                details, status = st.columns([3, 1])
                with details:
                    st.subheader(record.get("equipment_type", "未知设备"))
                    st.caption(f"创建时间：{record.get('created_at', '')}")
                with status:
                    st.write(f"处理状态：{record.get('status', '待处理')}")
                st.write(f"故障描述：{record.get('fault_description', '')}")
                with st.expander("查看分析结果"):
                    st.markdown(record.get("analysis_result", ""))

else:
    st.title("工业设备智能运维助手")
    st.caption("基于本地设备维护知识库与大语言模型，为常见工业设备故障提供辅助分析与排查建议。")
    st.caption("知识库检索 · 历史案例参考 · AI辅助分析 · 维护记录")
    with st.container(border=True):
        st.subheader("故障诊断工作台")
        st.caption("1 输入故障 → 2 补充信息（如需要） → 3 分析")
        equipment_type = st.selectbox("设备类型", ["三相异步电机", "PLC", "低压电气控制回路"])
        fault_description = st.text_area("故障描述", height=160, placeholder="例如：按下启动按钮后，接触器能够正常吸合，但电机不转。")
        start_analysis = st.button("开始分析", type="primary", use_container_width=True)

    if start_analysis:
        if not fault_description.strip():
            st.warning("请先填写故障描述。")
        else:
            with st.spinner("正在判断故障信息是否足够..."):
                relevance = evaluate_fault_relevance(equipment_type, fault_description)
            st.session_state.original_fault_description = fault_description
            st.session_state.analysis_equipment_type = equipment_type
            st.session_state.analysis_fault_description = fault_description
            st.session_state.analysis_result = ""
            st.session_state.analysis_started_with_supplement = False
            st.session_state.waiting_for_supplement = False
            if not relevance["relevant"]:
                st.session_state.analysis_result = ""
                st.warning("当前描述似乎与所选设备的故障或运行异常无关，请重新描述设备出现的异常现象。")
            else:
                with st.spinner("正在判断故障信息是否足够..."):
                    evaluation = evaluate_fault_information(equipment_type, fault_description)
            if relevance["relevant"] and evaluation["sufficient"]:
                try:
                    with st.spinner("正在进行故障分析..."):
                        data = run_rag_analysis(equipment_type, fault_description)
                    (st.session_state.debug_knowledge, st.session_state.debug_chunks,
                     st.session_state.debug_relevant_chunks, st.session_state.debug_similar_records,
                     st.session_state.analysis_result) = data
                except (ValueError, OSError) as error:
                    st.error("知识资料读取失败，请确认对应知识文件可用后重试。")
                except Exception as error:
                    st.error("分析请求失败，请检查服务配置或网络连接后重试。")
            elif relevance["relevant"]:
                st.session_state.waiting_for_supplement = True
                st.session_state.agent_question = evaluation.get("question", "请补充更多故障现象。")
                st.session_state.supplemental_information = ""

    if st.session_state.waiting_for_supplement:
        st.subheader("需要补充故障信息")
        st.info("当前阶段：2 / 3 · 补充信息。Agent 判断当前故障信息不足。")
        st.write("为了更准确地分析，请补充以下信息：")
        st.write(st.session_state.agent_question)
        st.session_state.supplemental_information = st.text_area(
            "补充信息", value=st.session_state.supplemental_information, height=120
        )
        if st.button("继续分析", type="primary", use_container_width=True):
            supplement = st.session_state.supplemental_information.strip()
            if not supplement:
                st.warning("请先填写补充信息。")
            else:
                complete_fault = (
                    f"原始故障描述：{st.session_state.original_fault_description}\n"
                    f"补充信息：针对‘{st.session_state.agent_question}’，用户回答：{supplement}"
                )
                # 保存和后续诊断都使用包含补充信息的完整描述。
                st.session_state.analysis_fault_description = complete_fault
                st.session_state.waiting_for_supplement = False
                st.session_state.analysis_started_with_supplement = True
                try:
                    with st.spinner("已结合补充信息进行故障分析..."):
                        data = run_rag_analysis(st.session_state.analysis_equipment_type, complete_fault)
                    (st.session_state.debug_knowledge, st.session_state.debug_chunks,
                     st.session_state.debug_relevant_chunks, st.session_state.debug_similar_records,
                     st.session_state.analysis_result) = data
                except (ValueError, OSError) as error:
                    st.error("知识资料读取失败，请确认对应知识文件可用后重试。")
                except Exception as error:
                    st.error("分析请求失败，请检查服务配置或网络连接后重试。")

    if st.session_state.analysis_started_with_supplement:
        st.info("已结合补充信息进行故障分析。")
    if st.session_state.analysis_result:
        st.divider()
        st.subheader("故障辅助分析结果")
        st.caption(f"本次分析设备：{st.session_state.analysis_equipment_type}")
        st.write("本次分析参考：")
        local_info, history_info = st.columns(2)
        with local_info:
            st.info("本地知识库：" + ("已检索" if st.session_state.debug_relevant_chunks else "未检索到高相关内容"))
        with history_info:
            count = len(st.session_state.debug_similar_records)
            st.info(f"历史案例：找到 {count} 条" if count else "历史案例：未找到相关案例")
        with st.container(border=True):
            # 保留模型原始 Markdown，不解析或改写诊断内容。
            st.markdown(st.session_state.analysis_result)
        if st.button("保存为维护记录"):
            save_maintenance_record(
                st.session_state.analysis_equipment_type,
                st.session_state.analysis_fault_description,
                st.session_state.analysis_result,
            )
            st.success("维护记录已保存")
        show_debug_information(
            st.session_state.debug_knowledge,
            st.session_state.debug_chunks,
            st.session_state.debug_relevant_chunks,
            st.session_state.debug_similar_records,
        )
