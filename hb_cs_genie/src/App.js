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
  const API_ENDPOINT = 'https://api.example.com'
  const handleSubmit = async (e) => {
    e.preventDefault()
    setStatus('submitting')
    setError('')
    try {
      const response = await fetch(`${API_ENDPOINT}/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
      })
      if (!response.ok) throw new Error('Failed to submit question')
      const data = await response.json()
      setId(data.id)
      setStatus('polling')
    } catch (err) {
      setError('Failed to submit question. Please try again.')
      setStatus('idle')
    }
  }

  useEffect(() => {
    if (status !== 'polling') return
    const pollStatus = async () => {
      try {
        const response = await fetch(`${API_ENDPOINT}/status/${id}`)
        if (!response.ok) throw new Error('Failed to fetch status')
        const data = await response.json()
        if (data.status === 'completed') {
          setStatus('fetching')
        } else {
          setTimeout(pollStatus, 2000) // Poll every 2 seconds
        }
      } catch (err) {
        setError('Failed to check status. Please try again.')
        setStatus('idle')
      }
    }
    pollStatus()
  }, [id, status])

  useEffect(() => {
    if (status !== 'fetching') return
    const fetchAnswer = async () => {
      try {
        const response = await fetch(`${API_ENDPOINT}/answer/${id}`)
        if (!response.ok) throw new Error('Failed to fetch answer')
        const data = await response.json()
        setAnswer(data.answer)
        setStatus('completed')
      } catch (err) {
        setError('Failed to fetch answer. Please try again.')
        setStatus('idle')
      }
    }
    fetchAnswer()
  }, [id, status])

  // const responseText = "Here are the key points about handling payroll corrections after December: \n\n * Complete all payroll corrections before December 31, 2024 as an off-cycle payroll to ensure correct recording on 2024 payroll reports \n\n * After December 31st, any adjustments to 2024 wages will require W-2 corrections and tax filing amendments\n * Homebase charges a $200 fee for amendments, so it's strongly recommended to submit corrections before December 31st\n\nIf you need to request a correction for 2024 after December 31st, provide:* Employee Name\n * Earning Hours\n * Earning Amount\n * Earning Type (regular, overtime, bonus, etc.)\n * Tax Breakdown\nImportant notes:\n * If you don't have tax breakdown, Homebase can calculate it for you\n * Corrections are processed on a first-come-first-serve basis\n * Current wait time for completed corrections and amended tax forms is 4-8 weeks\n---\nFor more information, see:\n[Correction payrolls after December 29th](https://support.joinhomebase.com/s/article/Correction-payrolls-after-December-29th)\n[Payroll Corrections with Homebase Payroll](https://support.joinhomebase.com/s/article/Payroll-Corrections-with-Homebase-Payroll)\n"
  const responseText = "For payroll corrections after December 31, 2024, here's what you need to do:\n\n1. Send an email to payroll@joinhomebase.com with the following information:\n* Employee Name\n* Earning Hours\n* Earning Amount\n* Earning Type (regular, overtime, bonus, etc.)\n* Tax Breakdown\n\nImportant notes:\n* Corrections after December 31st will require W-2 amendments for impacted employees\n* Homebase charges a $200 fee per quarter for amendments to closed tax quarters\n* Current wait time for completed corrections and amended tax forms is 4-8 weeks\n* If you don't have tax breakdown information, Homebase can calculate it for you\n\n---\n\nFor more information, see:\n[Correction payrolls after December 29th](https://support.joinhomebase.com/s/article/Correction-payrolls-after-December-29th)\n[Payroll Corrections with Homebase Payroll](https://support.joinhomebase.com/s/article/Payroll-Corrections-with-Homebase-Payroll)"

  return (
    <MantineProvider theme={DEFAULT_THEME}>
      <Box className="parent-root">
        <Title>Homebase Genie</Title>

        <Box className="search-box" style={{ padding: "10px 10px 20px 0px"}}>
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
        {status === 'completed' && (
          <Box bg="#eae7e7" style={{border: "2px", borderRadius: "15px", padding: " 2px 15px 2px 15px"}}>
            <h4 className="font-semibold">
              {question}
            </h4>
            <Text>
              <ReactMarkdown>
                { responseText }
              </ReactMarkdown>
            </Text>
          </Box>
        )}

        { error && <p className="mt-4 text-red-500">{error}</p> }
      </Box>
    </MantineProvider>
  )
}

export default App;
