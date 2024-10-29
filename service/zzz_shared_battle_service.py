from fastapi import FastAPI, File, UploadFile, Query, HTTPException
from fastapi.responses import FileResponse
from zzz_data_model import get_battle_info, get_battle_url
from zzz_save_battle_class import save_battle
from datetime import datetime
import os

# 初始化 FastAPI 应用
app = FastAPI()


# 查询全部数据的接口
@app.post("/getBattleInfo")
async def read_battle_info():
    return {"data": get_battle_info(), "msg": "查询成功"}


# 上传文件并处理的接口
@app.post("/uploadBattleInfo")
async def upload_battle_info(
        file: UploadFile = File(...),
        battle_name: str = Query(..., description="配置名称"),
        creation_name: str = Query(..., description="上传者名称")
):
    return await save_battle(battle_name, file, creation_name, datetime.now())


# 下载文件的接口
@app.get("/downloadBattleInfo/{bid}")
async def download_battle_info(bid: int):
    # 根据ID查询数据
    battle_info = get_battle_url(bid)

    if not battle_info:
        return HTTPException(status_code=400, detail="数据不存在")

    # 获取文件路径
    file_path = battle_info.battle_url
    if not os.path.exists(file_path):
        return HTTPException(status_code=400, detail="文件不存在")

    # 返回文件响应
    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type='application/x-yaml'
    )


# 运行应用
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
