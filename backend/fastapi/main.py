from fastapi import FastAPI

app = FastAPI()

# get method
@app.get("/")
def root():
    return {"message": "PipelineDoctor API running 🚀"}