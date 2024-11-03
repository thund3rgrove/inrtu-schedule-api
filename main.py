from fastapi import FastAPI, HTTPException
from utils import get_data, scrape_groups
import uvicorn
from starlette.responses import FileResponse 

app = FastAPI()
BASE_LINK = "https://istu.edu/schedule"

@app.get("/groups")
async def get_groups():
    try:
        groups = await scrape_groups(f"{BASE_LINK}?subdiv=683")
        return groups
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        # print(e)

@app.get("/schedule/{group_number}")
async def get_schedule(group_number: str):
    url = f"{BASE_LINK}?group={group_number}"
    try:
        schedule = await get_data(url)
        return schedule
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/')
async def serve_schedule():
    return FileResponse('index.html')

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
