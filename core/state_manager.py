"""
State Manager for Agents
管理Agent状态和共享数据
"""

import sqlite3
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path


class StateManager:
    """Agent状态管理器"""

    def __init__(self, db_path: str):
        """
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.db = None
        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self.db = sqlite3.connect(self.db_path)
        self.db.row_factory = sqlite3.Row

        cursor = self.db.cursor()

        # 创建states表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS states (
                agent_id TEXT PRIMARY KEY,
                state_data TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建messages表（Agent间通信）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_agent TEXT NOT NULL,
                to_agent TEXT NOT NULL,
                message_type TEXT NOT NULL,
                message_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed BOOLEAN DEFAULT FALSE
            )
        """)

        # 创建opportunities表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                market_id TEXT NOT NULL,
                opportunity_type TEXT NOT NULL,
                analysis_data TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.db.commit()

    def set_agent_state(self, agent_id: str, state_data: Dict[str, Any]) -> bool:
        """
        设置Agent状态

        Args:
            agent_id: Agent ID
            state_data: 状态数据字典

        Returns:
            是否成功
        """
        try:
            cursor = self.db.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO states (agent_id, state_data, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (agent_id, json.dumps(state_data)))

            self.db.commit()
            return True

        except Exception as e:
            print(f"设置Agent状态失败: {str(e)}")
            return False

    def get_agent_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        获取Agent状态

        Args:
            agent_id: Agent ID

        Returns:
            状态数据字典
        """
        try:
            cursor = self.db.cursor()

            cursor.execute("""
                SELECT state_data FROM states WHERE agent_id = ?
            """, (agent_id,))

            row = cursor.fetchone()

            if row:
                return json.loads(row["state_data"])
            else:
                return None

        except Exception as e:
            print(f"获取Agent状态失败: {str(e)}")
            return None

    def send_message(self, from_agent: str, to_agent: str,
                   message_type: str, message_data: Dict[str, Any]) -> bool:
        """
        Agent间发送消息

        Args:
            from_agent: 发送方Agent ID
            to_agent: 接收方Agent ID
            message_type: 消息类型（opportunity, trade, alert, status等）
            message_data: 消息数据

        Returns:
            是否成功
        """
        try:
            cursor = self.db.cursor()

            cursor.execute("""
                INSERT INTO messages (from_agent, to_agent, message_type, message_data, created_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (from_agent, to_agent, message_type, json.dumps(message_data)))

            self.db.commit()
            return True

        except Exception as e:
            print(f"发送消息失败: {str(e)}")
            return False

    def get_messages(self, to_agent: str, message_type: Optional[str] = None,
                    unprocessed_only: bool = True, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取发给某个Agent的消息

        Args:
            to_agent: 接收方Agent ID
            message_type: 消息类型（可选）
            unprocessed_only: 是否只获取未处理的消息
            limit: 最大返回数量

        Returns:
            消息列表
        """
        try:
            cursor = self.db.cursor()

            query = """
                SELECT id, from_agent, to_agent, message_type, message_data, created_at
                FROM messages
                WHERE to_agent = ?
            """
            params = [to_agent]

            if message_type:
                query += " AND message_type = ?"
                params.append(message_type)

            if unprocessed_only:
                query += " AND processed = FALSE"
            else:
                query += " AND processed = TRUE"

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            messages = []
            for row in rows:
                messages.append({
                    "id": row["id"],
                    "from_agent": row["from_agent"],
                    "to_agent": row["to_agent"],
                    "message_type": row["message_type"],
                    "message_data": json.loads(row["message_data"]),
                    "created_at": row["created_at"]
                })

            return messages

        except Exception as e:
            print(f"获取消息失败: {str(e)}")
            return []

    def mark_message_processed(self, message_id: int) -> bool:
        """
        标记消息为已处理

        Args:
            message_id: 消息ID

        Returns:
            是否成功
        """
        try:
            cursor = self.db.cursor()

            cursor.execute("""
                UPDATE messages SET processed = TRUE WHERE id = ?
            """, (message_id,))

            self.db.commit()
            return True

        except Exception as e:
            print(f"标记消息失败: {str(e)}")
            return False

    def save_opportunity(self, market_id: str, opportunity_type: str,
                       analysis_data: Dict[str, Any]) -> bool:
        """
        保存机会到数据库

        Args:
            market_id: 市场ID
            opportunity_type: 机会类型
            analysis_data: 分析数据

        Returns:
            是否成功
        """
        try:
            cursor = self.db.cursor()

            cursor.execute("""
                INSERT INTO opportunities (market_id, opportunity_type, analysis_data, status, created_at)
                VALUES (?, ?, ?, 'pending', CURRENT_TIMESTAMP)
            """, (market_id, opportunity_type, json.dumps(analysis_data)))

            self.db.commit()
            return True

        except Exception as e:
            print(f"保存机会失败: {str(e)}")
            return False

    def get_pending_opportunities(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取待处理的机会

        Args:
            limit: 最大返回数量

        Returns:
            机会列表
        """
        try:
            cursor = self.db.cursor()

            cursor.execute("""
                SELECT id, market_id, opportunity_type, analysis_data, status, created_at
                FROM opportunities
                WHERE status = 'pending'
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()

            opportunities = []
            for row in rows:
                opportunities.append({
                    "id": row["id"],
                    "market_id": row["market_id"],
                    "opportunity_type": row["opportunity_type"],
                    "analysis_data": json.loads(row["analysis_data"]),
                    "status": row["status"],
                    "created_at": row["created_at"]
                })

            return opportunities

        except Exception as e:
            print(f"获取机会失败: {str(e)}")
            return []

    def update_opportunity_status(self, opportunity_id: int, status: str) -> bool:
        """
        更新机会状态

        Args:
            opportunity_id: 机会ID
            status: 新状态

        Returns:
            是否成功
        """
        try:
            cursor = self.db.cursor()

            cursor.execute("""
                UPDATE opportunities
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, opportunity_id))

            self.db.commit()
            return True

        except Exception as e:
            print(f"更新机会状态失败: {str(e)}")
            return False

    def get_all_agent_states(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有Agent的状态

        Returns:
            {agent_id: state_data}
        """
        try:
            cursor = self.db.cursor()

            cursor.execute("SELECT agent_id, state_data, updated_at FROM states")
            rows = cursor.fetchall()

            states = {}
            for row in rows:
                states[row["agent_id"]] = {
                    "state": json.loads(row["state_data"]),
                    "updated_at": row["updated_at"]
                }

            return states

        except Exception as e:
            print(f"获取所有状态失败: {str(e)}")
            return {}

    def cleanup_old_messages(self, days: int = 7) -> bool:
        """
        清理旧消息

        Args:
            days: 保留天数

        Returns:
            是否成功
        """
        try:
            cursor = self.db.cursor()

            cursor.execute("""
                DELETE FROM messages
                WHERE created_at < datetime('now', '-' || ? || ' days')
            """, (days,))

            self.db.commit()
            return True

        except Exception as e:
            print(f"清理旧消息失败: {str(e)}")
            return False

    def close(self):
        """关闭数据库连接"""
        if self.db:
            self.db.close()
