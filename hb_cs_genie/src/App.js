import './App.css';
import { useEffect, useState } from "react";
import ReactMarkdown from 'react-markdown';
import {
  Input,
  Button,
  Title,
  MantineProvider,
  Box,
  DEFAULT_THEME,
  Text,
  Group, TextInput, Grid, Center, Badge
} from "@mantine/core";

function App() {
  const [question, setQuestion] = useState('')
  const [id, setId] = useState(null)
  const [status, setStatus] = useState('completed')
  const [answer, setAnswer] = useState('')
  const [error, setError] = useState('')
  const API_ENDPOINT = 'http://127.0.0.1:8000'

  const pollForAnswer = async (id) => {
    try {
      const response = await fetch(`${API_ENDPOINT}/get_query?id=${id}`);
      if (!response.ok) throw new Error('Failed to fetch answer');
      const data = await response.json();

      console.log(data.status)
      switch (data.status) {
        case 'completed':
          setAnswer(data.answer);
          setStatus('answered');
          console.log(answer)
          break;
        case 'in-progress':
          // Continue polling after a delay
          setTimeout(() => pollForAnswer(id), 1000);
          break;
        case 'error':
          setError('An error occurred while processing your question.');
          setStatus('idle');
          break;
        default:
          setError('Unexpected response from server');
          setStatus('idle');
      }
    } catch (err) {
      setError('Failed to fetch answer. Please try again.');
      setStatus('idle');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    setStatus('submitting');
    setError(null);
    setAnswer(null);

    try {
      const response = await fetch(`${API_ENDPOINT}/submit_query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query_text: question })
      });

      if (!response.ok) throw new Error('Failed to submit question');
      const data = await response.json();
      setId(data.id);
      setStatus('polling');
      // Start polling for the answer
      pollForAnswer(data.id);
    } catch (err) {
      setError('Failed to submit question. Please try again.');
      setStatus('idle');
    }
  };

  return (
    <MantineProvider theme={DEFAULT_THEME}>
      <Box className="parent-root">
        <Title>Homebase Genie</Title>

        <Box className="search-box" style={{ padding: "10px 10px 20px 0px" }}>
          <TextInput
            onChange={(e) => setQuestion(e.target.value)}
            style={{
              backgroundColor: "#f0f0f0",
              padding: "2px",
              fontSize: "14px",
              border: "0px"
            }}
          />
          <Button onClick={handleSubmit} color="cyan" variant="filled">
            Search for answers
          </Button>
        </Box>

        {status === 'polling' && <p className="mt-4">Checking status...</p>}
        {status === 'fetching' && <p className="mt-4">Fetching answer...</p>}
        {(status === 'completed' && answer) && (
          <Box bg="#eae7e7" style={{ border: "2px", borderRadius: "15px", padding: " 2px 15px 2px 15px" }}>
            <h4 className="font-semibold">
              {question}
            </h4>
            <Text>
              <ReactMarkdown>
                {answer}
              </ReactMarkdown>
            </Text>
          </Box>
        )}

        {error && <p className="mt-4 text-red-500">{error}</p>}
      </Box>
    </MantineProvider>
  )
}

export default App;
