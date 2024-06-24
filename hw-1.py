import requests
from elasticsearch import Elasticsearch
import tiktoken


#Q1. Running Elastic
#Run Elastic Search 8.4.3, and get the cluster information. If you run it on localhost, this is how you do it:



# Define the curl command
curl_command = [
    "curl",
    "-k",
    "-u",
    "elastic:<>",
    "https://localhost:9200",
    "--cacert",
    "/workspaces/ll-zoomcamp/elasticsearch-8.4.3/config/certs/http_ca.crt"
]

# Run the curl command
result = subprocess.run(curl_command, capture_output=True, text=True)



# Parse the JSON response
response_json = json.loads(result.stdout)

# Print the "name" from the response "42f05b9372a9a4a470db3b52817899b99a76ee73"
print( "version.build_hash  : "+response_json["version"]["build_hash"])


# Step 1: Fetch the FAQ data
docs_url = 'https://github.com/DataTalksClub/llm-zoomcamp/blob/main/01-intro/documents.json?raw=1'
docs_response = requests.get(docs_url)
documents_raw = docs_response.json()

documents = []

for course in documents_raw:
    course_name = course['course']

    for doc in course['documents']:
        doc['course'] = course_name
        documents.append(doc)

# Step 2: Connect to Elasticsearch
es = Elasticsearch(
    hosts=["https://localhost:9200"],
    basic_auth=("elastic", "<>"),
    verify_certs=True,
    ca_certs="/workspaces/ll-zoomcamp/elasticsearch-8.4.3/config/certs/http_ca.crt"
)

# Step 3: Check if Elasticsearch is running
if es.ping():
    print("Connected to Elasticsearch")
else:
    print("Could not connect to Elasticsearch")
    exit(1)

# Step 4: Create an index with the appropriate mappings
es.options(ignore_status=[400]).indices.create(
    index='faqs',
    body={
        "mappings": {
            "properties": {
                "course": {"type": "keyword"},
                "question": {"type": "text"},
                "answer": {"type": "text"}
            }
        }
    }
)

# Step 5: Index the documents
for doc in documents:
    es.index(index='faqs', document=doc)

# Step 6: Perform a search with boosted 'question' field
query = {
    "query": {
        "multi_match": {
            "query": "How do I execute a command in a running docker container?",
            "fields": ["question^4", "text"],
            "type": "best_fields"
        }
    }
}

response = es.search(index="faqs", body=query)

top_hit = response['hits']['hits'][0]
print(f"Top result score: {top_hit['_score']}")
print(f"Top result document: {top_hit['_source']}")

# Step 7: Define the context and prompt templates
context_template = """
Q: {question}
A: {text}
""".strip()

prompt_template = """
You're a course teaching assistant. Answer the QUESTION based on the CONTEXT from the FAQ database.
Use only the facts from the CONTEXT when answering the QUESTION.

QUESTION: {question}

CONTEXT:
{context}
""".strip()

# Step 8: Define the question and context entries
question = "How do I execute a command in a running docker container?"

context_entries = [
    context_template.format(
        question="How do I debug a docker container?",
        text="Launch the container image in interactive mode and overriding the entrypoint, so that it starts a bash command.\ndocker run -it --entrypoint bash <image>\nIf the container is already running, execute a command in the specific container:\ndocker ps (find the container-id)\ndocker exec -it <container-id> bash\n(Marcos MJD)"
    ),
    context_template.format(
        question="How do Lambda container images work?",
        text="(Answer text here, not provided in the example output)"
    ),
    context_template.format(
        question="How do I copy files from a different folder into docker container’s working directory?",
        text="(Answer text here, not provided in the example output)"
    )
]

context = "\n\n".join(context_entries)

# Step 9: Construct the prompt
prompt = prompt_template.format(question=question, context=context)

print("Constructed Prompt:\n", prompt)

# Step 10: Tokenize the prompt using tiktoken
encoding = tiktoken.encoding_for_model("gpt-4o")
tokens = encoding.encode(prompt)
number_of_tokens = len(tokens)

print(f"Tokens: {tokens}")
print(f"Number of tokens in the prompt: {number_of_tokens}")

# Step 11: Perform a search with filter for 'machine-learning-zoomcamp'
query = {
    "query": {
        "bool": {
            "must": {
                "multi_match": {
                    "query": "How do I execute a command in a running docker container?",
                    "fields": ["question^4", "text"],
                    "type": "best_fields"
                }
            },
            "filter": {
                "term": {
                    "course": "machine-learning-zoomcamp"
                }
            }
        }
    },
    "size": 3
}

response = es.search(index="faqs", body=query)
hits = response['hits']['hits']

# Step 12: Build the context from the top 3 hits
context_entries = []

for hit in hits:
    source = hit['_source']
    context_entries.append(context_template.format(
        question=source['question'],
        text=source['text']
    ))

context = "\n\n".join(context_entries)

# Construct the prompt with new context
prompt = prompt_template.format(question=question, context=context)

length_of_prompt = len(prompt)
print(f"Length of the resulting prompt: {length_of_prompt}")

# Print the 3rd result's question
third_hit = hits[2]
print(f"3rd result question: {third_hit['_source']['question']}")
