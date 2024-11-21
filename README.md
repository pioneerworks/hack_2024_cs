# hack_2024_cs

### Using api_service.py
To start the service run the following command:

```uvicorn api_service.api_service:app --reload```

Examples of API calls to the service:

- POST
```
  curl -X POST "http://127.0.0.1:8000/submit_query" -H "Content-Type: application/json" -d '{"query_text": "Sample query2"}'
  ```
  response:
```
{"message":"Query submitted successfully","id":3}   
```
- GET
```
curl -X GET "http://127.0.0.1:8000/get_query?id=3"
```

response:
```
"This is a test response"
```

