import json
from typing import Any, Dict, Iterator, Optional, Sequence, Tuple
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    ChannelVersions,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
)
from app.core.supabase import get_supabase_client


class SupabaseCheckpointer(BaseCheckpointSaver):
    """
    Persists LangGraph checkpoints directly to Supabase context_threads/memory.
    Provides state durability across agent executions and human-in-the-loop approvals.
    """

    def __init__(self):
        super().__init__()

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        configurable = config.get("configurable", {})
        thread_id = configurable.get("thread_id")
        checkpoint_ns = configurable.get("checkpoint_ns", "")
        checkpoint_id = configurable.get("checkpoint_id")

        if not thread_id:
            return None

        try:
            supabase = get_supabase_client()
            query = (
                supabase.table("context_threads")
                .select("*")
                .eq("id", thread_id)
            )
            res = query.execute()
            if not res.data or len(res.data) == 0:
                return None

            record = res.data[0]
            metadata_blob = record.get("metadata") or {}
            saved_checkpoint = metadata_blob.get("checkpoint")
            if not saved_checkpoint:
                return None

            checkpoint_data: Checkpoint = json.loads(saved_checkpoint.get("checkpoint", "{}"))
            checkpoint_metadata: CheckpointMetadata = saved_checkpoint.get("metadata", {})
            parent_config = saved_checkpoint.get("parent_config")

            return CheckpointTuple(
                config=config,
                checkpoint=checkpoint_data,
                metadata=checkpoint_metadata,
                parent_config=parent_config,
            )
        except Exception:
            return None

    def list(
        self,
        config: Optional[RunnableConfig],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        if config:
            t = self.get_tuple(config)
            if t:
                yield t

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        configurable = config.get("configurable", {})
        thread_id = configurable.get("thread_id")
        checkpoint_ns = configurable.get("checkpoint_ns", "")

        if not thread_id:
            return config

        try:
            supabase = get_supabase_client()
            payload = {
                "checkpoint": json.dumps(checkpoint, default=str),
                "metadata": metadata,
                "parent_config": config,
            }

            # Update context_threads metadata
            existing = supabase.table("context_threads").select("metadata").eq("id", thread_id).execute()
            curr_meta = existing.data[0].get("metadata") if existing.data else {}
            curr_meta = curr_meta or {}
            curr_meta["checkpoint"] = payload

            supabase.table("context_threads").update({"metadata": curr_meta}).eq("id", thread_id).execute()
        except Exception:
            pass

        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint["id"],
            }
        }
