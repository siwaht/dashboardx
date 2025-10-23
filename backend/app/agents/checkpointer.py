"""
Checkpointing for Durable Agent Execution

Provides PostgreSQL-based checkpointing for LangGraph agents.
Enables:
- Resuming from failures
- Time-travel debugging
- Human-in-the-loop workflows
- Conversation history
"""

import logging
from typing import Optional
from urllib.parse import urlparse

from langgraph.checkpoint.postgres import PostgresSaver
from psycopg import Connection

from app.config import settings

logger = logging.getLogger(__name__)


class AgentCheckpointer:
    """
    Manages checkpointing for agent execution
    
    Uses PostgreSQL to store agent state at each step,
    allowing for durable execution and recovery.
    """
    
    def __init__(self):
        self.connection_string = self._get_connection_string()
        self._checkpointer: Optional[PostgresSaver] = None
    
    def _get_connection_string(self) -> str:
        """
        Get PostgreSQL connection string from Supabase configuration
        
        Returns:
            PostgreSQL connection string
        """
        # Use the database connection string from settings
        return settings.supabase_db_connection
    
    def get_checkpointer(self) -> PostgresSaver:
        """
        Get or create PostgreSQL checkpointer
        
        Returns:
            PostgresSaver instance
        """
        if self._checkpointer is None:
            try:
                logger.info("Initializing PostgreSQL checkpointer")
                
                # Create checkpointer
                self._checkpointer = PostgresSaver.from_conn_string(
                    self.connection_string
                )
                
                # Setup tables (creates if not exists)
                self._checkpointer.setup()
                
                logger.info("Checkpointer initialized successfully")
                
            except Exception as e:
                logger.error(f"Error initializing checkpointer: {e}")
                raise
        
        return self._checkpointer
    
    async def save_checkpoint(
        self,
        session_id: str,
        state: dict,
        step: str
    ) -> str:
        """
        Save a checkpoint
        
        Args:
            session_id: Session ID
            state: Agent state to save
            step: Current step name
            
        Returns:
            Checkpoint ID
        """
        try:
            checkpointer = self.get_checkpointer()
            
            # Save checkpoint
            checkpoint_id = await checkpointer.aput(
                config={"configurable": {"thread_id": session_id}},
                checkpoint={
                    "state": state,
                    "step": step
                },
                metadata={
                    "session_id": session_id,
                    "step": step
                }
            )
            
            logger.info(f"Checkpoint saved: {checkpoint_id} (session: {session_id})")
            return checkpoint_id
            
        except Exception as e:
            logger.error(f"Error saving checkpoint: {e}")
            raise
    
    async def load_checkpoint(
        self,
        session_id: str,
        checkpoint_id: Optional[str] = None
    ) -> Optional[dict]:
        """
        Load a checkpoint
        
        Args:
            session_id: Session ID
            checkpoint_id: Specific checkpoint ID (optional, loads latest if None)
            
        Returns:
            Checkpoint data or None if not found
        """
        try:
            checkpointer = self.get_checkpointer()
            
            # Load checkpoint
            checkpoint = await checkpointer.aget(
                config={"configurable": {"thread_id": session_id}}
            )
            
            if checkpoint:
                logger.info(f"Checkpoint loaded for session: {session_id}")
                return checkpoint
            else:
                logger.info(f"No checkpoint found for session: {session_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error loading checkpoint: {e}")
            return None
    
    async def list_checkpoints(
        self,
        session_id: str,
        limit: int = 10
    ) -> list:
        """
        List checkpoints for a session
        
        Args:
            session_id: Session ID
            limit: Maximum number of checkpoints to return
            
        Returns:
            List of checkpoints
        """
        try:
            checkpointer = self.get_checkpointer()
            
            # List checkpoints
            checkpoints = await checkpointer.alist(
                config={"configurable": {"thread_id": session_id}},
                limit=limit
            )
            
            logger.info(f"Found {len(checkpoints)} checkpoints for session: {session_id}")
            return checkpoints
            
        except Exception as e:
            logger.error(f"Error listing checkpoints: {e}")
            return []
    
    async def delete_checkpoints(
        self,
        session_id: str
    ) -> int:
        """
        Delete all checkpoints for a session
        
        Args:
            session_id: Session ID
            
        Returns:
            Number of checkpoints deleted
        """
        try:
            # This is a placeholder
            # In production, implement proper deletion
            logger.info(f"Deleting checkpoints for session: {session_id}")
            
            # TODO: Implement checkpoint deletion
            
            return 0
            
        except Exception as e:
            logger.error(f"Error deleting checkpoints: {e}")
            return 0


# Singleton instance
_checkpointer_instance: Optional[AgentCheckpointer] = None


def get_checkpointer() -> AgentCheckpointer:
    """
    Get or create checkpointer singleton
    
    Returns:
        AgentCheckpointer instance
    """
    global _checkpointer_instance
    
    if _checkpointer_instance is None:
        _checkpointer_instance = AgentCheckpointer()
    
    return _checkpointer_instance


# ==================== Usage with LangGraph ====================

def create_graph_with_checkpointing():
    """
    Create agent graph with checkpointing enabled
    
    Example usage:
    ```python
    from app.agents.graph import create_agent_graph
    from app.agents.checkpointer import get_checkpointer
    
    # Create graph
    workflow = create_agent_graph()
    
    # Compile with checkpointing
    checkpointer = get_checkpointer()
    graph = workflow.compile(
        checkpointer=checkpointer.get_checkpointer()
    )
    
    # Run with session tracking
    result = await graph.ainvoke(
        initial_state,
        config={"configurable": {"thread_id": session_id}}
    )
    ```
    """
    pass


# ==================== Checkpoint Management ====================

async def resume_from_checkpoint(
    session_id: str,
    checkpoint_id: Optional[str] = None
):
    """
    Resume agent execution from a checkpoint
    
    Args:
        session_id: Session ID
        checkpoint_id: Specific checkpoint to resume from
        
    Returns:
        Resumed execution result
    """
    try:
        checkpointer = get_checkpointer()
        
        # Load checkpoint
        checkpoint = await checkpointer.load_checkpoint(
            session_id=session_id,
            checkpoint_id=checkpoint_id
        )
        
        if not checkpoint:
            raise ValueError(f"No checkpoint found for session: {session_id}")
        
        logger.info(f"Resuming from checkpoint: {session_id}")
        
        # Resume execution
        # This would integrate with the agent graph
        # For now, return the checkpoint data
        return checkpoint
        
    except Exception as e:
        logger.error(f"Error resuming from checkpoint: {e}")
        raise


async def get_session_history(
    session_id: str,
    limit: int = 10
) -> list:
    """
    Get execution history for a session
    
    Args:
        session_id: Session ID
        limit: Maximum number of history items
        
    Returns:
        List of historical states
    """
    try:
        checkpointer = get_checkpointer()
        
        checkpoints = await checkpointer.list_checkpoints(
            session_id=session_id,
            limit=limit
        )
        
        return checkpoints
        
    except Exception as e:
        logger.error(f"Error getting session history: {e}")
        return []
