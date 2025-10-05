import React, { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import { Button, Navbar, Container, Card, Tabs, Tab, Form, ListGroup, Row, Col, CloseButton, Spinner } from 'react-bootstrap';
import ReactMarkdown from 'react-markdown';
import './App.css';

function App() {
  const [code, setCode] = useState('print("Hello, World!")');
  const [output, setOutput] = useState('');
  const [aiFeedback, setAiFeedback] = useState('');
  const [exercise, setExercise] = useState(null);
  const [activeTab, setActiveTab] = useState('exercise');
  const [solutionFeedback, setSolutionFeedback] = useState(null);
  const [interest, setInterest] = useState('');
  const [project, setProject] = useState(null);
  const [difficulty, setDifficulty] = useState('Beginner');
  const [explanation, setExplanation] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Automatically generate an exercise on first load
  useEffect(() => {
    handleGenerateExercise();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const clearOutput = () => {
    setOutput('');
    setAiFeedback('');
    setSolutionFeedback(null);
    setExplanation('');
  }

  const handleRunCode = async () => {
    setIsLoading(true);
    setOutput(''); // Clear previous run output
    setActiveTab('output');

    try {
      const response = await fetch('http://localhost:8000/api/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      });

      if (!response.body) return;

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }
        const chunk = decoder.decode(value);
        setOutput((prev) => prev + chunk);
      }

    } catch (error) {
        setOutput("Failed to execute code.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateExercise = async () => {
    setIsLoading(true);
    try {
      clearOutput();
      setExercise(null);
      setActiveTab('exercise');
      const response = await fetch('http://localhost:8000/api/generate-exercise', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ difficulty }),
      });
      const data = await response.json();
      setExercise(data);

      const functionNameMatch = data.description?.match(/`(\w+)\(.*\)`/);
      if (functionNameMatch && functionNameMatch[1]) {
        setCode(`def ${functionNameMatch[1]}():\n  # Your code here\n  pass\n`);
      } else {
        setCode(`# Solve the exercise for a ${difficulty} level.`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleCheckSolution = async () => {
    if (!exercise) return;
    setIsLoading(true);
    try {
      setSolutionFeedback(null);
      setActiveTab('output');
      const response = await fetch('http://localhost:8000/api/check-solution', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ code, exercise }),
      });
      const data = await response.json();
      setSolutionFeedback(data);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateProject = async () => {
    if (!interest) return;
    setIsLoading(true);
    try {
      setProject(null);
      const response = await fetch('http://localhost:8000/api/generate-project', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ interest }),
      });
      const data = await response.json();
      setProject(data);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExplainCode = async () => {
    if (!code) return;
    setIsLoading(true);
    try {
      setExplanation('');
      setActiveTab('output');
      const response = await fetch('http://localhost:8000/api/explain-code', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ code }),
      });
      const data = await response.json();
      setExplanation(data.explanation);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="App">
      <Navbar bg="dark" variant="dark">
        <Container>
          <Navbar.Brand href="#home">AI Python Course</Navbar.Brand>
        </Container>
      </Navbar>
      <div className="main-content">
        <div className="editor-container">
          <Editor
            height="100%"
            defaultLanguage="python"
            theme="vs-dark"
            value={code}
            onChange={(value) => setCode(value || '')}
          />
          <div className="control-bar">
            <Button variant="secondary" onClick={handleExplainCode} disabled={isLoading}>Explain Code</Button>
            <Button variant="secondary" onClick={handleCheckSolution} disabled={!exercise || isLoading}>Check Solution</Button>
            <Button variant="primary" onClick={handleRunCode} disabled={isLoading}>Run Code</Button>
          </div>
        </div>
        <div className="right-panel" style={{ position: 'relative' }}>
          {isLoading && (
            <div className="loading-overlay">
              <Spinner animation="border" role="status" variant="light">
                <span className="visually-hidden">Loading...</span>
              </Spinner>
            </div>
          )}
          <Tabs activeKey={activeTab} onSelect={(k) => setActiveTab(k)} id="output-tabs" className="mb-3">
            <Tab eventKey="exercise" title="Exercise" disabled={isLoading}>
              <div className="p-3">
                <Form as={Row} className="g-2 align-items-center mb-3">
                  <Col xs="auto">
                    <Form.Label className="mb-0">Difficulty:</Form.Label>
                  </Col>
                  <Col>
                    <Form.Select value={difficulty} onChange={(e) => setDifficulty(e.target.value)} size="sm" disabled={isLoading}>
                      <option>Beginner</option>
                      <option>Intermediate</option>
                      <option>Advanced</option>
                    </Form.Select>
                  </Col>
                  <Col xs="auto">
                    <Button variant="secondary" onClick={handleGenerateExercise} disabled={isLoading}>New Exercise</Button>
                  </Col>
                </Form>
                <hr />
                {exercise ? (
                  <Card>
                    <Card.Header as="h5">{exercise.title}</Card.Header>
                    <Card.Body>
                      <Card.Text as="div" dangerouslySetInnerHTML={{ __html: exercise.description?.replace(/`([^`]+)`/g, '<code>$1</code>') }} />
                    </Card.Body>
                  </Card>
                ) : (
                  <p>Loading exercise...</p>
                )}
              </div>
            </Tab>
            <Tab eventKey="output" title="Output" disabled={isLoading}>
              <div className="p-3">
                <div className="d-flex justify-content-between align-items-center mb-2">
                  <h5 className="mb-0">Output</h5>
                  <CloseButton onClick={clearOutput} title="Clear Output" />
                </div>
                {explanation && (
                  <Card className="mb-3">
                    <Card.Header as="h5">💡 Code Explanation</Card.Header>
                    <Card.Body>
                      <ReactMarkdown>{explanation}</ReactMarkdown>
                    </Card.Body>
                  </Card>
                )}
                {solutionFeedback && (
                  <Card className="mb-3">
                    <Card.Header as="h5" className={solutionFeedback.is_correct ? 'text-success' : 'text-danger'}>
                      {solutionFeedback.is_correct ? '✅ Correct Solution' : '❌ Keep Trying!'}
                    </Card.Header>
                    <Card.Body>
                      <Card.Text>{solutionFeedback.feedback}</Card.Text>
                    </Card.Body>
                  </Card>
                )}
                {(output || aiFeedback) && (
                  <Card className="mt-3">
                    <Card.Header as="h5">▶️ Run Result</Card.Header>
                    <Card.Body>
                      {output && <pre className="output-pre">{output}</pre>}
                      {aiFeedback && (
                        <div className="mt-2">
                          <strong>🤖 AI Tutor Feedback:</strong>
                          <p>{aiFeedback}</p>
                        </div>
                      )}
                    </Card.Body>
                  </Card>
                )}
              </div>
            </Tab>
            <Tab eventKey="projects" title="Projects" disabled={isLoading}>
              <div className="p-3">
                  <Form.Group className="mb-3">
                      <Form.Label>Enter an interest to generate a project idea:</Form.Label>
                      <Form.Control 
                          type="text" 
                          placeholder="e.g., gaming, space, music" 
                          value={interest}
                          onChange={(e) => setInterest(e.target.value)}
                          disabled={isLoading}
                      />
                  </Form.Group>
                  <Button variant="primary" onClick={handleGenerateProject} disabled={!interest || isLoading}>Generate Project</Button>
                  
                  {project && (
                      <Card className="mt-4">
                          <Card.Header as="h5">{project.title}</Card.Header>
                          <Card.Body>
                              <Card.Text>{project.description}</Card.Text>
                              <h6 className="mt-3">Features:</h6>
                              <ListGroup>
                                  {project.features?.map((feature, index) => (
                                      <ListGroup.Item key={index}>{feature}</ListGroup.Item>
                                  ))}
                              </ListGroup>
                          </Card.Body>
                      </Card>
                  )}
              </div>
            </Tab>
          </Tabs>
        </div>
      </div>
    </div>
  );
}

export default App;
