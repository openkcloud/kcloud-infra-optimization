from fastapi import FastAPI
import uvicorn

app = FastAPI(title="kcloud-simulator")

@app.get("/")
async def root():
    return {"service": "simulator", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "simulator"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8009)