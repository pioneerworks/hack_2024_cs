from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

app = FastAPI()

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class CsHelpAgentQueries(Base):
    __tablename__ = "cs_help_agent_queries"
    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(Text, nullable=False)
    response_received = Column(Boolean, nullable=False)
    response_text = Column(Text, nullable=True)

Base.metadata.create_all(bind=engine)

class QueryRequest(BaseModel):
    query_text: str

def process_query_text(query_text: str) -> str:
    # the calls to the LLM should go here
    return f"This is a test response"

def update_query_response(query_id: int, query_text: str):
    db = SessionLocal()
    response_text = process_query_text(query_text)
    query = db.query(CsHelpAgentQueries).filter(CsHelpAgentQueries.id == query_id).first()
    query.response_text = response_text
    query.response_received = True
    db.commit()
    db.close()

@app.post("/submit_query")
async def submit_query(query_request: QueryRequest, background_tasks: BackgroundTasks):
    db = SessionLocal()
    new_query = CsHelpAgentQueries(
        query_text=query_request.query_text,
        response_received=False,
        response_text=str(None)
    )
    db.add(new_query)
    db.commit()
    db.refresh(new_query)
    background_tasks.add_task(update_query_response, new_query.id, query_request.query_text)
    db.close()
    return {"message": "Query submitted successfully", "id": new_query.id}

@app.get("/get_query")
async def get_query(id: int):
    db = SessionLocal()
    query = db.query(CsHelpAgentQueries).filter(CsHelpAgentQueries.id == id).first()
    db.close()
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
    # return {"id": query.id, "query_text": query.query_text, "response_received": query.response_received, "response_text": query.response_text}
    # In case you want to pull any elements of the response, here is how you can access those
    return query.response_text

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)