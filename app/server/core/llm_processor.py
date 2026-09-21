import os
from typing import Dict, Any
from openai import OpenAI
from anthropic import Anthropic
from core.data_models import QueryRequest

def generate_sql_with_openai(query_text: str, schema_info: Dict[str, Any]) -> str:
    """
    Generate SQL query using OpenAI API
    """
    try:
        # Get API key from environment
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        client = OpenAI(api_key=api_key)
        
        # Format schema for prompt
        schema_description = format_schema_for_prompt(schema_info)
        
        # Create prompt
        prompt = f"""Given the following database schema:

{schema_description}

Convert this natural language query to SQL: "{query_text}"

Rules:
- Return ONLY the SQL query, no explanations
- Use proper SQLite syntax
- Handle date/time queries appropriately (e.g., "last week" = date('now', '-7 days'))
- Be careful with column names and table names
- If the query is ambiguous, make reasonable assumptions
- For multi-table queries, use proper JOIN conditions to avoid Cartesian products
- Limit results to reasonable amounts (e.g., add LIMIT 100 for large result sets)
- When joining tables, use meaningful relationships between tables

SQL Query:"""
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are a SQL expert. Convert natural language to SQL queries."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        sql = response.choices[0].message.content.strip()
        
        # Clean up the SQL (remove markdown if present)
        if sql.startswith("```sql"):
            sql = sql[6:]
        if sql.startswith("```"):
            sql = sql[3:]
        if sql.endswith("```"):
            sql = sql[:-3]
        
        return sql.strip()
        
    except Exception as e:
        raise Exception(f"Error generating SQL with OpenAI: {str(e)}")

def generate_sql_with_anthropic(query_text: str, schema_info: Dict[str, Any]) -> str:
    """
    Generate SQL query using Anthropic API
    """
    try:
        # Get API key from environment
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        client = Anthropic(api_key=api_key)
        
        # Format schema for prompt
        schema_description = format_schema_for_prompt(schema_info)
        
        # Create prompt
        prompt = f"""Given the following database schema:

{schema_description}

Convert this natural language query to SQL: "{query_text}"

Rules:
- Return ONLY the SQL query, no explanations
- Use proper SQLite syntax
- Handle date/time queries appropriately (e.g., "last week" = date('now', '-7 days'))
- Be careful with column names and table names
- If the query is ambiguous, make reasonable assumptions
- For multi-table queries, use proper JOIN conditions to avoid Cartesian products
- Limit results to reasonable amounts (e.g., add LIMIT 100 for large result sets)
- When joining tables, use meaningful relationships between tables

SQL Query:"""
        
        # Call Anthropic API
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=500,
            temperature=0.1,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        sql = response.content[0].text.strip()
        
        # Clean up the SQL (remove markdown if present)
        if sql.startswith("```sql"):
            sql = sql[6:]
        if sql.startswith("```"):
            sql = sql[3:]
        if sql.endswith("```"):
            sql = sql[:-3]
        
        return sql.strip()
        
    except Exception as e:
        raise Exception(f"Error generating SQL with Anthropic: {str(e)}")

def format_schema_for_prompt(schema_info: Dict[str, Any]) -> str:
    """
    Format database schema for LLM prompt
    """
    lines = []
    
    for table_name, table_info in schema_info.get('tables', {}).items():
        lines.append(f"Table: {table_name}")
        lines.append("Columns:")
        
        for col_name, col_type in table_info['columns'].items():
            lines.append(f"  - {col_name} ({col_type})")
        
        lines.append(f"Row count: {table_info['row_count']}")
        lines.append("")
    
    return "\n".join(lines)

def truncate_to_two_sentences(text: str) -> str:
    """
    Defensive safety net that enforces a maximum of two sentences.
    Splits on '.', '!', '?' terminators and reassembles at most the first two.
    """
    text = text.strip()

    sentences = []
    current = ""
    for char in text:
        current += char
        if char in ".!?":
            sentences.append(current.strip())
            current = ""
            if len(sentences) == 2:
                break

    # If there's leftover text and we haven't hit the limit, no terminal
    # punctuation was found for it, so leave the text unchanged.
    if not sentences:
        return text

    if len(sentences) < 2 and current.strip():
        return text

    return " ".join(sentences)

def generate_random_query_with_openai(schema_info: Dict[str, Any]) -> str:
    """
    Generate a random natural language query suggestion using OpenAI API
    """
    try:
        # Get API key from environment
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        client = OpenAI(api_key=api_key)

        # Format schema for prompt
        schema_description = format_schema_for_prompt(schema_info)

        # Create prompt
        prompt = f"""Given the following database schema:

{schema_description}

Suggest one interesting, specific natural language question a user could ask about this data. Reference real table and column names, and favor questions that involve aggregations, filters, or comparisons that are actually answerable given the schema.

Rules:
- Return ONLY the natural language question, no explanations or quotes
- Do not include SQL syntax
- Limit your response to two sentences maximum

Question:"""

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are a data analyst who suggests interesting natural language questions about a given database schema."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )

        question = response.choices[0].message.content.strip()

        # Clean up the question (remove markdown if present)
        if question.startswith("```sql"):
            question = question[6:]
        if question.startswith("```"):
            question = question[3:]
        if question.endswith("```"):
            question = question[:-3]

        return truncate_to_two_sentences(question.strip())

    except Exception as e:
        raise Exception(f"Error generating random query with OpenAI: {str(e)}")

def generate_random_query_with_anthropic(schema_info: Dict[str, Any]) -> str:
    """
    Generate a random natural language query suggestion using Anthropic API
    """
    try:
        # Get API key from environment
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        client = Anthropic(api_key=api_key)

        # Format schema for prompt
        schema_description = format_schema_for_prompt(schema_info)

        # Create prompt
        prompt = f"""Given the following database schema:

{schema_description}

Suggest one interesting, specific natural language question a user could ask about this data. Reference real table and column names, and favor questions that involve aggregations, filters, or comparisons that are actually answerable given the schema.

Rules:
- Return ONLY the natural language question, no explanations or quotes
- Do not include SQL syntax
- Limit your response to two sentences maximum

Question:"""

        # Call Anthropic API
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=500,
            temperature=0.7,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        question = response.content[0].text.strip()

        # Clean up the question (remove markdown if present)
        if question.startswith("```sql"):
            question = question[6:]
        if question.startswith("```"):
            question = question[3:]
        if question.endswith("```"):
            question = question[:-3]

        return truncate_to_two_sentences(question.strip())

    except Exception as e:
        raise Exception(f"Error generating random query with Anthropic: {str(e)}")

def generate_random_query(schema_info: Dict[str, Any], llm_provider: str = "openai") -> str:
    """
    Generate a random natural language query suggestion based on the current schema.
    Route to appropriate LLM provider based on API key availability and preference.
    Priority: 1) OpenAI API key exists, 2) Anthropic API key exists, 3) llm_provider preference
    """
    if not schema_info.get('tables'):
        raise Exception("No tables available to generate a query suggestion")

    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

    # Check API key availability first (OpenAI priority)
    if openai_key:
        return generate_random_query_with_openai(schema_info)
    elif anthropic_key:
        return generate_random_query_with_anthropic(schema_info)

    # Fall back to request preference if both keys available or neither available
    if llm_provider == "openai":
        return generate_random_query_with_openai(schema_info)
    else:
        return generate_random_query_with_anthropic(schema_info)

def generate_sql(request: QueryRequest, schema_info: Dict[str, Any]) -> str:
    """
    Route to appropriate LLM provider based on API key availability and request preference.
    Priority: 1) OpenAI API key exists, 2) Anthropic API key exists, 3) request.llm_provider
    """
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    
    # Check API key availability first (OpenAI priority)
    if openai_key:
        return generate_sql_with_openai(request.query, schema_info)
    elif anthropic_key:
        return generate_sql_with_anthropic(request.query, schema_info)
    
    # Fall back to request preference if both keys available or neither available
    if request.llm_provider == "openai":
        return generate_sql_with_openai(request.query, schema_info)
    else:
        return generate_sql_with_anthropic(request.query, schema_info)