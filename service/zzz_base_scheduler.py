from apscheduler.schedulers.asyncio import AsyncIOScheduler
from zzz_syn_battle_service import SynBattle
import asyncio

# 创建后台调度器
scheduler = AsyncIOScheduler()
syn_battle = SynBattle()

# 添加任务，每60秒执行一次
scheduler.add_job(syn_battle.fetch_data, 'interval', seconds=60)

# 启动调度器
scheduler.start()

try:
    asyncio.get_event_loop().run_forever()
except (KeyboardInterrupt, SystemExit):
    # 当接收到中断信号时，关闭调度器
    scheduler.shutdown()
