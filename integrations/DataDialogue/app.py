from fastapi import FastAPI, Query
from pydantic import BaseModel
import google.generativeai as genai
from sqlalchemy import create_engine, text, MetaData
import os

# Create a FastAPI instance
app = FastAPI()

# Configure Generative AI API with the provided API key
genai.configure(api_key=os.getenv("API_KEY"))

# Define a Pydantic model for the input data
class QueryInput(BaseModel):
    uri: str
    query: str

# Function to generate text using Generative AI
def generate_text(prompt):
    # Initialize a GenerativeModel instance
    model = genai.GenerativeModel()
    
    # Generate content based on the given prompt
    response = model.generate_content(
        prompt,
        generation_config={
            "max_output_tokens": 2048,
            "temperature": 0.4,
            "top_p": 1,
            "top_k": 32,
        },
    )
    
    # Return the generated text
    return response.text

# Function to connect to the database
def connect_to_database(uri):
    try:
        # Create a SQLAlchemy engine using the provided URI
        engine = create_engine(uri)
        metadata = MetaData()
        
        # Reflect the metadata of the database
        metadata.reflect(bind=engine)
        
        # Write table information to a file
        with open("./docs/tableInfo.txt", 'w') as f:
            for table_name, table in metadata.tables.items():
                f.write(f"Table: {table_name}\n")
                f.write("Columns")
            
                # Write column information
                for column in table.c:
                    f.write(f"\tName: {column.name}\n")
                    f.write(f"\tType: {column.type}\n")
                    f.write(f"\tNullable: {column.nullable}\n")
                    f.write(f"\tPrimary Key: {column.primary_key}\n")
                    f.write(f"\tForeign Key: {column.foreign_keys}\n") 
                    f.write("\n")
                f.write("Constraints:\n")
                
                # Write constraint information
                for constraint in table.constraints:
                    f.write(f"\t {constraint}\n")
        # Return the database engine
        return engine
    except Exception as e:
        # Return None in case of any exceptions
        return None
    
# Function to execute SQL query
def execute_query(engine, query):
    try:
        # Connect to the database engine
        conn = engine.connect()
        # Create a SQLAlchemy text object for the query
        query_text = text(query)
        # Execute the query and get the result
        result = conn.execute(query_text)
        # Return the query result
        return result
    except Exception as e:
        # Return None in case of any exceptions
        return None

# Endpoint to execute SQL queries
@app.get('/execute')
async def get_output(username: str = Query(...), password: str = Query(...), host: str = Query(...), port: int = Query(...), dbname: str = Query(...), query: str = Query(...), dbtype: str = Query(...)):
    # Construct database URI
    uri = f"{dbtype}://{username}:{password}@{host}:{port}/{dbname}"
    print(uri)
    dbtype = uri.split(":")[0]
    
    # Read instructions from a file
    with open("./docs/instructions.txt", "r") as f:
        instructions = f.read()
        
    # Read table information from a file
    with open("./docs/tableInfo.txt", "r") as f:
        table_info = f.read()
        
    # Connect to the database
    engine = connect_to_database(uri)  
    
    # Construct prompt for Generative AI
    prompt = f"write {dbtype} query  starting with ```sql only and not anything else and ending with ``` to do following operation {query} and table schema info is {table_info}"
    prompt += f"Instructions: {instructions}"
    
    # Generate text using Generative AI
    generated_text = generate_text(prompt=prompt)
    print(generate_text)
    query_generated = generated_text.split("```sql")[1][:-3]
    print(query_generated)
    result = execute_query(engine, query_generated)
    print(result)
    
    # Generate human-readable answer
    answer = ""
    for row in result:
        answer += str(row)
    answer = generate_text(f"User Query: {query} Answer {answer} write the answer in proper statements about what user asked keeping it in a human-readable manner")
    print(answer)
    
    # Return the response
    return {"response": answer}
