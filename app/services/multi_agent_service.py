"""多Agent编排服务"""
from typing import Dict, Optional, TypedDict, List, Any
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

class AgentState(TypedDict):
    """Agent状态定义"""
    messages: List[str]
    task_type: str
    evidence: Optional[Dict[str, Any]]
    result: Optional[str]

class MultiAgentOrchestrator:
    """多Agent编排器"""
    
    def __init__(self, llm_config: Optional[Dict] = None):
        """
        初始化多Agent编排器
        
        Args:
            llm_config: LLM配置字典
        """
        self.llm_config = llm_config or {}
        
        if llm_config and llm_config.get('baseUrl'):
            self.llm = ChatOpenAI(
                base_url=llm_config.get('baseUrl'),
                model=llm_config.get('modelId', 'gpt-4'),
                api_key=llm_config.get('apiKey', 'sk-xxx'),
                temperature=0.1
            )
        else:
            self.llm = None
    
    def task_sorting_node(self, state: AgentState) -> AgentState:
        """任务分类节点"""
        task_type = state.get('task_type', 'general')
        state['messages'].append(f"任务分类: {task_type}")
        return state
    
    def standard_interpretation_node(self, state: AgentState) -> AgentState:
        """标准解读节点"""
        if self.llm:
            prompt = f"请解读以下标准要求：{state.get('task_type', '')}"
            response = self.llm.invoke(prompt)
            state['messages'].append(f"标准解读: {response.content}")
        else:
            state['messages'].append("标准解读: LLM未配置")
        return state
    
    def evidence_review_node(self, state: AgentState) -> AgentState:
        """证据审核节点"""
        evidence = state.get('evidence', {})
        if evidence:
            state['messages'].append(f"证据审核: 审核证据 {evidence.get('name', '未知')}")
            state['result'] = "审核完成"
        else:
            state['messages'].append("证据审核: 无证据")
            state['result'] = "需要提供证据"
        return state
    
    def build_graph(self):
        """构建Agent工作流图"""
        workflow = StateGraph(AgentState)
        
        # 添加节点
        workflow.add_node("task_sorting", self.task_sorting_node)
        workflow.add_node("standard_interpretation", self.standard_interpretation_node)
        workflow.add_node("evidence_review", self.evidence_review_node)
        
        # 添加边
        workflow.add_edge("task_sorting", "standard_interpretation")
        workflow.add_edge("standard_interpretation", "evidence_review")
        workflow.add_edge("evidence_review", END)
        
        # 设置入口点
        workflow.set_entry_point("task_sorting")
        
        return workflow.compile()
    
    def run(self, task_type: str, evidence: Optional[Dict] = None) -> Dict[str, Any]:
        """
        运行多Agent工作流
        
        Args:
            task_type: 任务类型
            evidence: 证据信息
            
        Returns:
            执行结果
        """
        if not self.llm:
            return {"error": "LLM未配置，无法运行Agent"}
        
        try:
            graph = self.build_graph()
            initial_state: AgentState = {
                "messages": [],
                "task_type": task_type,
                "evidence": evidence,
                "result": None
            }
            
            final_state = graph.invoke(initial_state)
            
            return {
                "messages": final_state["messages"],
                "result": final_state["result"],
                "status": "success"
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "failed"
            }
    
    def is_available(self) -> bool:
        """检查服务是否可用"""
        return self.llm is not None
