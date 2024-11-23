import './App.css';
import { useEffect, useState } from "react";
import ReactMarkdown from 'react-markdown';
import {
  Button,
  Title,
  MantineProvider,
  Box,
  Text,
  TextInput,
  Container,
} from "@mantine/core";
import { IconSearch } from '@tabler/icons-react';
import { ThreeDot } from 'react-loading-indicators'

function App() {
  const [question, setQuestion] = useState('')
  const [currentQuestion, setCurrentQuestion] = useState('')
  const [id, setId] = useState(null)
  const [status, setStatus] = useState('completed')
  const [answer, setAnswer] = useState('')
  const [error, setError] = useState('')
  const API_ENDPOINT = 'http://127.0.0.1:8000'
  const [qaHistory, setQaHistory] = useState([]);

  useEffect(() => {
    if (status !== 'in-progress') { return }

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
            setQaHistory(prevHistory => [{
              question: currentQuestion,
              answer: data.answer
            }, ...prevHistory]);
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

    // Add this line to actually start polling
    pollForAnswer(id);

    // Add cleanup function
    return () => {
      // Clean up any pending timeouts if component unmounts
      clearTimeout();
    };
  }, [status, answer, id, currentQuestion]); // Add id and currentQuestion to dependencies

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim() || status === 'in-progress') return;

    setCurrentQuestion(question);
    setQuestion('');
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
      setStatus('in-progress');
    } catch (err) {
      setError('Failed to submit question. Please try again.');
      setStatus('idle');
    }
  };

  return (
    <MantineProvider>
      <Container
        size="xl"
        style={{
          minHeight: '100vh',
          backgroundColor: '#f1edff',
          padding: '40px 20px'
        }}
      >
        {/* Title Section */}
        <Box style={{ textAlign: 'center', marginBottom: '60px' }}>
          <Title
            order={1}
            className="title-wrapper"
            style={{
              fontSize: '2.5rem',
              marginBottom: '0px',
              display: 'inline-block'
            }}
          >
            <span className="title-text">
              Homebase Genie
            </span>
            <div className="line-reveal" />
          </Title>
          <Text size="lg" style={{ color: '#6b6b6b' }}>
            Built by Queryous Minds and LLMs.
          </Text>
        </Box>

        {/* Search Input Section */}
        <Box
          style={{
            maxWidth: '600px',
            margin: '0 auto',
            position: 'relative',
            display: 'flex',
            gap: '10px'
          }}
        >
          <form onSubmit={handleSubmit}>
            <Box style={{ display: 'flex', gap: '10px' }}>
              <TextInput
                placeholder="Enter your Homebase-related question here..."
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                disabled={status === 'in-progress'}
                styles={{
                  input: {
                    height: '45px',
                    borderRadius: '12px',
                    border: '1px solid #e0e0e0',
                    fontSize: '16px',
                    width: '460px',
                    '&:focus': {
                      borderColor: '#8B5CF6',
                    },
                    '&:disabled': {
                      backgroundColor: '#f5f5f5',
                      cursor: 'not-allowed'
                    },
                    paddingLeft: '20px',
                    paddingRight: '20px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis'
                  },
                  wrapper: {
                    width: '450px',
                  }
                }}
              />
              <Button
                type="submit"
                className={`search-button ${status === 'in-progress' ? 'loading' : ''}`}
                disabled={!question.trim() || status === 'in-progress'}
                loading={status === 'in-progress'}
                style={{
                  backgroundColor: '#4B0082',
                  height: '48px',
                  padding: '0 30px',
                  borderRadius: '14px',
                  fontSize: '16px',
                  fontWeight: '500',
                  cursor: status === 'in-progress' ? 'not-allowed' : 'pointer',
                  border: 'none',
                  color: 'white',
                  marginLeft: '60px',
                }}
                styles={{
                  root: {
                    '&:hover': {
                      backgroundColor: '#7C3AED',
                    },
                    '&:disabled': {
                      backgroundColor: '#E9ECEF',
                      color: '#ADB5BD',
                    }
                  },
                }}
              >
                <IconSearch size={20} />
              </Button>
            </Box>
          </form>
        </Box>

        {/* Results Section */}
        <Box style={{ maxWidth: '600px', margin: '20px auto' }}>
          {status === 'in-progress' && (
            <Box style={{ display: 'flex', justifyContent: 'center', marginTop: '30px', marginBottom: '30px' }}>
              <ThreeDot color="#8B5CF6" size="small" text="" textColor="#8B5CF6" />
            </Box>
          )}

          {qaHistory.map((qa, index) => (
            <Box
              key={index}
              style={{
                backgroundColor: 'white',
                borderRadius: '20px',
                padding: '20px',
                marginTop: '20px',
                boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)'
              }}
            >
              <Text
                size="lg"
                mb={10}
                style={{
                  fontWeight: 700,  // Make question bold
                  color: '#1a1a1a',  // Darker color for better contrast
                  fontSize: '14px'
                }}
              >
                {qa.question}
              </Text>
              <Box
                style={{
                  marginTop: '5px',
                  borderTop: '1px solid #f0f0f0',
                  paddingTop: '5px',
                  fontSize: '14px'
                }}
              >
                <ReactMarkdown
                  components={{
                    a: ({ node, ...props }) => (
                      <a {...props} target="_blank" rel="noopener noreferrer" />
                    )
                  }}
                >
                  {qa.answer}
                </ReactMarkdown>
              </Box>
            </Box>
          ))}
        </Box>
      </Container>
    </MantineProvider>
  );
}

export default App;
