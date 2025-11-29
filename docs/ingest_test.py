import requests

files = [
    ('files', open('E:\RAG\Enterprise Knowledge Base RAG Assistant\docs\Customer Support Knowledge Base FAQ PDF.pdf', 'rb')),
    ('files', open('E:\RAG\Enterprise Knowledge Base RAG Assistant\docs\Product Requirements Document PDF.pdf', 'rb')),
    ('files', open('docs/EnterpriCorp Employee Handbook Comprehensive Draft.pdf', 'rb')),

]

response = requests.post("http://127.0.0.1:8000/ingest", files=files)
print(response.json())