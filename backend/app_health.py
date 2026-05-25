from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "✓ Viral Video SaaS is running!", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
