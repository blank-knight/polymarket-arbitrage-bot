"""
Base Agent Class
所有Agent的基类，提供通用功能
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from core.state_manager import StateManager


class BaseAgent(ABC):
    """Agent基类"""

    def __init__(self, agent_id: str, state_manager: StateManager, config: Dict[str, Any]):
        """
        Args:
            agent_id: Agent ID
            state_manager: 状态管理器
            config: 配置字典
        """
        self.agent_id = agent_id
        self.state_manager = state_manager
        self.config = config
        self.enabled = config.get("enabled", True)

        # 加载Agent状态
        self.state = self._load_state()

    @abstractmethod
    def run(self) -> None:
        """Agent主运行方法，由子类实现"""
        pass

    @abstractmethod
    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理收到的消息

        Args:
            message: 消息字典

        Returns:
            响应字典
        """
        pass

    def _load_state(self) -> Dict[str, Any]:
        """加载Agent状态"""
        state = self.state_manager.get_agent_state(self.agent_id)

        if state is None:
            # 初始化默认状态
            state = self._init_default_state()
            self.state_manager.set_agent_state(self.agent_id, state)
            return state

        return state

    def _init_default_state(self) -> Dict[str, Any]:
        """初始化默认状态，子类可以覆盖"""
        return {
            "status": "idle",
            "last_run": None,
            "data": {}
        }

    def _save_state(self, state: Optional[Dict[str, Any]] = None):
        """保存Agent状态"""
        if state:
            self.state = state

        self.state_manager.set_agent_state(self.agent_id, self.state)

    def _update_state_field(self, key: str, value: Any):
        """更新状态中的某个字段"""
        self.state["data"][key] = value
        self.state_manager.set_agent_state(self.agent_id, self.state)

    def send_message(self, to_agent: str, message_type: str, message_data: Dict[str, Any]) -> bool:
        """
        发送消息给其他Agent

        Args:
            to_agent: 目标Agent ID
            message_type: 消息类型
            message_data: 消息数据

        Returns:
            是否成功
        """
        return self.state_manager.send_message(
            from_agent=self.agent_id,
            to_agent=to_agent,
            message_type=message_type,
            message_data=message_data
        )

    def get_messages(self, message_type: Optional[str] = None) -> list:
        """
        获取发给自己的消息

        Args:
            message_type: 消息类型（可选）

        Returns:
            消息列表
        """
        return self.state_manager.get_messages(
            to_agent=self.agent_id,
            message_type=message_type
        )

    def check_enabled(self) -> bool:
        """检查Agent是否启用"""
        return self.enabled and self.config.get("enabled", True)

    def log(self, level: str, message: str):
        """日志"""
        timestamp = self.state.get("last_run", "N/A")
        print(f"[{self.agent_id}][{level}][{timestamp}] {message}")

    def set_status(self, status: str):
        """设置状态"""
        from datetime import datetime

        self.state["status"] = status
        self.state["last_run"] = datetime.now().isoformat()
        self._save_state()

    def get_status(self) -> str:
        """获取状态"""
        return self.state.get("status", "idle")
