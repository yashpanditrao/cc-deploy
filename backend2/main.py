import requests
import os
from dotenv import load_dotenv
import google.generativeai as genai
import json
from supabase import create_client, Client
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
port = os.getenv("PORT")
pplx = os.getenv("PERPLEXITY_API_KEY")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
friday_api_key = os.getenv("FRIDAY_API_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")

app = FastAPI()

# Add CORS middleware with complete configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "https://cc-deploy-pi.vercel.app"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=86400,  # Cache preflight requests for 24 hours
)

# Pydantic models for request validation
class WebsiteRequest(BaseModel):
    url: str

class QueryRequest(BaseModel):
    url: Optional[str] = None
    summary: Optional[str] = None

class ChatMessage(BaseModel):
    message: str
    conversation_state: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    next_question: Optional[str] = None
    conversation_state: str
    is_complete: bool = False
    company_info: Optional[dict] = None

class CompanyInfoRequest(BaseModel):
    company_name: str
    description: str
    target_market: str
    problem_and_solution: str  # Combined problem and solution
    business_model: str
    current_stage: str

class CompetitorSearch(BaseModel):
    summary: str
    queries: List[str]

class VCFirmRequest(BaseModel):
    sectors: List[str]
    stage: str

class ComparisonRequest(BaseModel):
    url1: str
    url2: str

class VCSearchRequest(BaseModel):
    name: str

# Add routes before the existing functions
@app.get("/")
def read_root():
    return {"message": "Welcome to the Information Density API"}

@app.post("/analyze")
async def analyze_endpoint(request: WebsiteRequest):
    result = analyze_website(request.url)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/generate-queries")
async def queries_endpoint(request: QueryRequest):
    if request.url:
        # If URL is provided, analyze website first
        result = analyze_website(request.url)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        summary = result['website_analysis']['summary']
    elif request.summary:
        # If summary is provided directly, use it
        summary = request.summary
    else:
        raise HTTPException(status_code=422, detail="Either url or summary must be provided")
    
    queries = get_queries(summary)
    return {"queries": queries}

@app.post("/search-competitors")
async def competitors_endpoint(request: CompetitorSearch):
    competitors = search_competitors(request.summary, request.queries)
    return {"competitors": competitors}

@app.post("/vc-firms")
async def vcfirms_endpoint(request: VCFirmRequest):
    firms = vcfirms(request.sectors, request.stage)
    return {"firms": firms}

@app.post("/compare")
async def compare_endpoint(request: ComparisonRequest):
    comparison = compare_websites(request.url1, request.url2)
    if "error" in comparison:
        raise HTTPException(status_code=400, detail=comparison["error"])
    return comparison

@app.post("/chat")
async def chat_endpoint(request: ChatMessage):
    response = process_chat_message(request.message, request.conversation_state)
    return response

@app.post("/analyze-company-info")
async def analyze_company_info_endpoint(request: CompanyInfoRequest):
    result = analyze_company_info(request)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/find-vc")
async def find_vc_endpoint(request: VCSearchRequest):
    profiles = look_for_vc(request.name)
    return {"profiles": profiles}
    

def look_for_vc(name: str):
    supabase = create_client(supabase_url, supabase_key)
    """
    Search for VC profiles on LinkedIn and store in Supabase
    
    Args:
        name (str): Name to search for
        
    Returns:
        list: Up to 2 LinkedIn profile links with snippets
    """
    api_url = 'https://friday-data-production.up.railway.app/search'
    headers = {
        'accept': 'application/json',
        'X-API-Key': friday_api_key,
        'Content-Type': 'application/json'
    }
    
    payload = {
        "query": f"{name} linkedin",
        "location": "US",
        "num_results": 15
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        print(response.json())
        response.raise_for_status()
        search_results = response.json().get('results', [])
        
        # Filter for LinkedIn URLs that don't contain "company"
        vc_profiles = []
        for result in search_results:
            url = result.get('url', '')  # Changed from 'link' to 'url' based on response format
            if 'linkedin.com' in url.lower() and 'company' not in url.lower() and 'posts' not in url.lower() and 'newsletters' not in url.lower() and 'blog' not in url.lower() and 'pulse' not in url.lower():
                vc_profiles.append({
                    'link': url,
                    'snippet': result.get('snippet', '')
                })
                if len(vc_profiles) == 2:  # Limit to 2 results
                    break
        
        # Update Supabase
        supabase.table('investors').update({
            'profiles': vc_profiles
        }).eq('name', name).execute()
                    
        return vc_profiles
        
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return []

def scrape_website(site_url):
    """
    Scrape a website using the Friday API endpoint
    """
    api_url = 'https://friday-data-production.up.railway.app/scrape'
    
    headers = {
        'accept': 'application/json',
        'X-API-Key': friday_api_key,
        'Content-Type': 'application/json'
    }
    
    payload = {
        'url': site_url,
        'format': 'markdown'
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        
        # Debug print
        print("API Response Status:", response.status_code)
        
        # Convert response to JSON
        response_json = response.json()
        
        # Debug print
        print("Response content type:", type(response_json))
        
        if isinstance(response_json, dict) and 'markdown' in response_json:
            return response_json['markdown']
        else:
            # If API response doesn't contain markdown, create simulated markdown
            return f"# {site_url}\n\nContent could not be retrieved properly."
            
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def structured_data(response):
    """
    Process scraped website data through Gemini API
    
    Args:
        response (dict): The scraped website data
        
    Returns:
        str: Structured response from Gemini
    """
   

    genai.configure(api_key=gemini_api_key)

    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40, 
        "max_output_tokens": 8192,
        "response_mime_type": "application/json",
    }

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
    )

    chat_session = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": [
                    response,
                    """provide the following in structured output based on the following:
                    {
                        industry: specific industry value,
                        solution: text in solution that they are proposing,
                        summary: summary of the site,
                        sectors: choose what type of VC firm sectors they are in (choose 1-3 in array format (always include Sector Agnostic)):
                        [
                            "Sector Agnostic",
                            "Social Impact",
                            "B2B Commerce",
                            "Consumer",
                            "Logistics",
                            "Mobility",
                            "DeepTech",
                            "Fintech",
                            "Edtech",
                            "AI/ML",
                            "AR/VR",
                            "Agritech/Food",
                            "Biotech/Life sciences",
                            "Climate/Sustainability",
                            "Deep Tech/Hard Science",
                            "Education",
                            "Enterprise",
                            "Media & Entertainment",
                            "Gaming",
                            "Government/Defence",
                            "Health and Wellness",
                            "Healthcare/Medtech",
                            "Industrial/IoT/ Robotics",
                            "Prop Tech/Real Estate",
                            "SaaS/DevOps/Marketplace",
                            "Supply Chain/Logistics",
                            "Travel/Hospitality"
                        ]
                    }"""
                ],
            },
        ]
    )

    response = chat_session.send_message("Please analyze the provided content")
    return response.text



def get_industry_market_size(industry_name: str, api_key: str) -> dict:
    url = "https://api.perplexity.ai/chat/completions"
    
    payload = {
        "model": "sonar",
        "messages": [
            {
                "role": "system",
                "content": """Analyze the market size of the specified industry and return a paragraph with the following information:
                - Market size in billions USD
                - Year of the estimate
                - Annual growth rate as a percentage
                - Brief explanation of the figures
                - Cite reliable sources"""
            },
            {
                "role": "user",
                "content": f"What is the current market size of the {industry_name} industry? Include global market value, growth rate, and cite reliable sources."
            }
        ],
        "max_tokens": 500,
        "temperature": 0.2,
        "top_p": 0.9,
        "return_images": False,
        "stream": False
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        return {
            "market_analysis": result['choices'][0]['message']['content'],
            "citations": result.get('citations', [])
        }
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse response: {str(e)}"}

def analyze_website(site_url: str) -> dict:
    """
    Analyze a website by combining scraping, structured data analysis, and market research
    
    Args:
        site_url (str): The URL to analyze
        
    Returns:
        dict: Combined analysis results
    """
    # Scrape the website
    scraped_data = scrape_website(site_url)
    if not scraped_data:
        return {"error": "Failed to scrape website"}
    
    # Get structured data from Gemini
    structured_result = structured_data(scraped_data)
    try:
        structured_info = json.loads(structured_result)
    except json.JSONDecodeError:
        return {"error": "Failed to parse structured data"}
    
    # Get market size information
    market_info = get_industry_market_size(
        structured_info.get('industry', 'technology'), 
        pplx
    )
    
    # Combine all results
    final_result = {
        "website_url": site_url,
        "website_analysis": structured_info,
        "market_analysis": market_info
    }
    
    return final_result

def get_queries(summary):
    """
    Generate 2 search queries based on the provided summary to identify competitors.
    
    Args:
        summary (str): The summary of the company or product.
        
    Returns:
        list: A list of 2 search queries.
    """
    genai.configure(api_key=gemini_api_key)

    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "application/json",
    }

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
    )

    chat_session = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": [
                    summary,
                    "Generate a list of 2 Google search queries to identify competitors, focus on 1 key feature per query nothing more nothing else, without directly looking for competitors by name. Return the queries as a structured array in the format: [q1, q2]. EXAMPLE: AI powered startup investor matching platform or Postgres SQL Backend as a service",
                ],
            },
        ]
    )

    response = chat_session.send_message("Please generate the search queries")
    try:
        queries = json.loads(response.text)
        return queries
    except json.JSONDecodeError:
        return ["Error: Failed to generate search queries"]


def search_competitors(summary, queries):
    """
    Search for competitors using the generated queries and return the top 5 competitors with links.
    
    Args:
        summary (str): The summary of the company or product.
        queries (list): A list of search queries.
        
    Returns:
        list: A list of top 5 competitors with links.
    """
    api_url = 'https://friday-data-production.up.railway.app/search'
    headers = {
        'accept': 'application/json',
        'X-API-Key': friday_api_key,
        'Content-Type': 'application/json'
    }
    competitors = []

    for query in queries:
        payload = {
            "query": query,
            "location": "US",
            "num_results": 10
        }
        try:
            response = requests.post(api_url, headers=headers, json=payload)
            response.raise_for_status()
            search_results = response.json().get('results', [])
            competitors.extend(search_results)
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")

    # Pass the search results and initial summary to the LLM to identify actual competitors
    competitors_summary = "\n".join([f"{result['title']}: {result['snippet']} (URL: {result['url']})" for result in competitors])
    genai.configure(api_key=gemini_api_key)

    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "application/json",
    }

    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        generation_config=generation_config,
    )

    chat_session = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": [
                    summary,
                    competitors_summary,
                    "Identify the top 5 actual competitors from the provided search results, considering the initial summary. Return the competitors in the format: [{name: 'Competitor Name', link: 'website url'}]",
                ],
            },
        ]
    )

    response = chat_session.send_message("Please identify the top 5 competitors")
    try:
        top_competitors = json.loads(response.text)
        return top_competitors
    except json.JSONDecodeError:
        return ["Error: Failed to identify competitors"]

def vcfirms(sectors, stage):
    supabase = create_client(supabase_url, supabase_key)

    # Convert sectors and stage to lowercase
    sectors = [s.lower() for s in sectors]
    stage = stage.lower()

    try:
        # Query the database
        response = supabase.table('investors').select('name, ticket_size, current_fund_corpus, logo_url, sector_focus, stage_focus').execute()
        
        investors = response.data
        filtered_investors = []

        for investor in investors:
            investor_sectors = [s.lower() for s in investor.get('sector_focus', [])]
            investor_stages = [s.lower() for s in investor.get('stage_focus', [])]
            
            if any(s in investor_sectors for s in sectors) and stage in investor_stages:
                filtered_investors.append(investor)

        # Limit the results to 10 VC firms
        return filtered_investors[:10]
    except Exception as e:
        print(f"Error querying database: {e}")
        return []

def compare_websites(url1: str, url2: str) -> dict:
    """
    Compare two websites by scraping their content and generating a tabular comparison
    
    Args:
        url1 (str): First URL to compare
        url2 (str): Second URL to compare
        
    Returns:
        dict: Comparison results in a structured format
    """
    # Scrape both websites
    data1 = scrape_website(url1)
    data2 = scrape_website(url2)
    
    if not data1 or not data2:
        return {"error": "Failed to scrape one or both websites"}
    
    # Get structured data for both websites
    structured1 = structured_data(data1)
    structured2 = structured_data(data2)
    
    try:
        info1 = json.loads(structured1)
        info2 = json.loads(structured2)
    except json.JSONDecodeError:
        return {"error": "Failed to parse structured data"}

    # Use Gemini to generate comparison
    genai.configure(api_key=gemini_api_key)

    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "application/json",
    }

    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        generation_config=generation_config,
    )

    comparison_prompt = f"""
    Compare these two companies based on their website data:

    Company 1: {json.dumps(info1)}
    Company 2: {json.dumps(info2)}

    Generate a structured comparison in the following JSON format:
    {{
        "comparison_table": [
            {{
                "aspect": "Industry",
                "company1": "value for company 1",
                "company2": "value for company 2"
            }},
            {{
                "aspect": "Solution",
                "company1": "value for company 1",
                "company2": "value for company 2"
            }},
            {{
                "aspect": "Target Market",
                "company1": "value for company 1",
                "company2": "value for company 2"
            }},
            {{
                "aspect": "Key Differentiators",
                "company1": "value for company 1",
                "company2": "value for company 2"
            }},
            {{
                "aspect": "Competitive Advantage",
                "company1": "value for company 1",
                "company2": "value for company 2"
            }}
        ],
        "summary": "A brief summary of key differences and similarities"
    }}
    """

    chat = model.start_chat()
    response = chat.send_message(comparison_prompt)
    
    try:
        comparison_result = json.loads(response.text)
        return {
            "url1": url1,
            "url2": url2,
            "comparison": comparison_result
        }
    except json.JSONDecodeError:
        return {"error": "Failed to generate comparison"}

def analyze_company_info(company_info: CompanyInfoRequest) -> dict:
    """
    Analyze company information provided through conversation
    
    Args:
        company_info (CompanyInfoRequest): The company information provided by the founder
        
    Returns:
        dict: Analysis results in the same format as website analysis
    """
    # Format the company information for Gemini
    company_description = f"""
    Company Name: {company_info.company_name}
    Description: {company_info.description}
    Target Market: {company_info.target_market}
    Problem and Solution: {company_info.problem_and_solution}
    Business Model: {company_info.business_model}
    Current Stage: {company_info.current_stage}
    """
    
    # Get structured data using Gemini
    structured_result = structured_data(company_description)
    try:
        structured_info = json.loads(structured_result)
    except json.JSONDecodeError:
        return {"error": "Failed to parse structured data"}
    
    # Get market size information
    market_info = get_industry_market_size(
        structured_info.get('industry', 'technology'), 
        pplx
    )
    
    # Combine all results
    final_result = {
        "website_url": None,
        "website_analysis": structured_info,
        "market_analysis": market_info
    }
    
    return final_result

def generate_chat_response(state: str, company_info: dict = None, user_message: str = None) -> str:
    """
    Generate dynamic chat responses using Gemini
    """
    genai.configure(api_key=gemini_api_key)
    
    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 1024,
    }

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
    )

    if not state or state == "awaiting_name":
        prompt = """
        You are a friendly startup advisor. Generate a warm, engaging greeting and ask for the company name.
        Keep it casual but professional. Vary your response each time.
        Example: "Hi there! I'm excited to learn about your startup journey. What's the name of your company?"
        Response should be just the greeting and question, nothing else.
        """
    else:
        # Format collected info for context
        info_context = "Information collected so far:\n"
        if company_info:
            for key, value in company_info.items():
                info_context += f"{key}: {value}\n"

        prompts = {
            "awaiting_description": f"""
                {info_context}
                Generate an engaging response acknowledging the company name and ask about what the company does.
                Be enthusiastic but professional. Make it conversational.
                Example: "That's a great name! Tell me more about what [company] does."
                Response should be just the acknowledgment and question, nothing else.
            """,
            "awaiting_target_market": f"""
                {info_context}
                Generate an engaging response that shows understanding of their business and ask about their target market.
                Be specific based on their description. Make it conversational.
                Example: "Interesting approach! Who are the main customers or users you're targeting with this solution?"
                Response should be just the acknowledgment and question, nothing else.
            """,
            "awaiting_problem_solution": f"""
                {info_context}
                Generate an engaging response that acknowledges their target market and ask about both the problem they're solving and their solution.
                Be specific based on their previous answers. Make it conversational.
                Example: "I see you're focusing on [market]. What specific problem are you solving for them, and how does your solution address it?"
                Response should be just the acknowledgment and question, nothing else.
            """,
            "awaiting_business_model": f"""
                {info_context}
                Generate an engaging response that acknowledges their solution and ask about their business model.
                Be specific based on their previous answers. Make it conversational.
                Example: "Your approach sounds innovative! How do you plan to monetize this solution?"
                Response should be just the acknowledgment and question, nothing else.
            """,
            "awaiting_stage": f"""
                {info_context}
                Generate an engaging response that acknowledges their business model and ask about their current stage.
                Be specific based on their previous answers. Make it conversational.
                Remind them to choose from: Pre-Seed, Seed, Series A, or Series B.
                Example: "Interesting business model! What stage is your startup in currently? (Pre-Seed/Seed/Series A/Series B)"
                Response should be just the acknowledgment and question, nothing else.
            """
        }

        prompt = prompts.get(state, "I couldn't process that. Let's start over. What's your company name?")

    chat = model.start_chat()
    response = chat.send_message(prompt)
    return response.text.strip()

def process_chat_message(message: str, state: Optional[str] = None) -> ChatResponse:
    """
    Process chat messages and guide the conversation to gather company information
    """
    if not state:
        # Start of conversation
        response = generate_chat_response(None)
        return ChatResponse(
            response=response,
            next_question="What's your company name?",
            conversation_state="awaiting_name"
        )
    
    conversation_flow = {
        "awaiting_name": {
            "next_state": "awaiting_description",
            "field": "company_name"
        },
        "awaiting_description": {
            "next_state": "awaiting_target_market",
            "field": "description"
        },
        "awaiting_target_market": {
            "next_state": "awaiting_problem_solution",
            "field": "target_market"
        },
        "awaiting_problem_solution": {
            "next_state": "awaiting_business_model",
            "field": "problem_and_solution"
        },
        "awaiting_business_model": {
            "next_state": "awaiting_stage",
            "field": "business_model"
        },
        "awaiting_stage": {
            "next_state": "complete",
            "field": "current_stage"
        }
    }

    current_flow = conversation_flow.get(state)
    if not current_flow:
        response = generate_chat_response(None)
        return ChatResponse(
            response=response,
            next_question="What's your company name?",
            conversation_state="awaiting_name"
        )

    # Initialize or update company info
    company_info = {}
    if state != "awaiting_name":
        try:
            company_info = json.loads(message.split("|||")[1])
        except:
            company_info = {}
    
    # Update company info with new information
    company_info[current_flow["field"]] = message.split("|||")[0] if "|||" in message else message

    if current_flow["next_state"] == "complete":
        # Validate stage input
        stage = company_info["current_stage"].strip().lower()
        valid_stages = {"pre-seed", "seed", "series a", "series b"}
        if stage not in valid_stages:
            return ChatResponse(
                response="Please enter a valid stage (Pre-Seed/Seed/Series A/Series B)",
                next_question="What stage is your company in?",
                conversation_state="awaiting_stage",
                company_info=company_info
            )
        
        # Return final response and end conversation
        return ChatResponse(
            response="Thank you for sharing all the information about your company. I'll now analyze this data to provide insights about your business.",
            conversation_state="complete",
            is_complete=True,
            company_info=company_info
        )

    # Generate dynamic response based on current state and collected info
    response = generate_chat_response(current_flow["next_state"], company_info, message)
    
    return ChatResponse(
        response=response,
        next_question=None,  # We don't need this anymore since responses are dynamic
        conversation_state=current_flow["next_state"],
        company_info=company_info
    )

# Modify the main block to run either CLI or API server
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "cli":
        # CLI mode
        stage = input("Enter what stage the company is in: ")
        site_url = input("Enter the website URL to analyze: ")
        result = analyze_website(site_url)
        queries = get_queries(result['website_analysis']['summary'])
        competitors = search_competitors(result['website_analysis']['summary'], queries)
        vcfirms_result = vcfirms(result['website_analysis']['sectors'], stage)
        print("\nAnalysis Results:")
        print(json.dumps(result, indent=2))
        print("\nSearch Queries:")
        print(queries)
        print("\nTop Competitors:")
        print(competitors)
        print("\nVC Firms:")
        print(vcfirms_result)
    else:
        # API mode
        uvicorn.run(app, host="0.0.0.0", port=port, reload=True)