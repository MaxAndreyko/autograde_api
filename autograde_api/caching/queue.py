import aioredis
import json

async def get_task_position(task_id: str, redis_client: aioredis.Redis, queue_name: str = "celery") -> int:
    """Get task's position in queue with proper FIFO calculation"""
    
    # Get all tasks and total count
    tasks = await redis_client.lrange(queue_name, 0, -1)
    total_tasks = len(tasks)
    
    for index, task in enumerate(tasks):
        try:
            task_data = json.loads(task)
            if task_data.get("headers", {}).get("id") == task_id:
                # Calculate position in execution order (FIFO)
                return total_tasks - index - 1
        except json.JSONDecodeError:
            continue
            
    return -1