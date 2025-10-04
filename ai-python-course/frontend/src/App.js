import React, { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import { Button, Navbar, Container, Card, Tabs, Tab } from 'react-bootstrap';
import './App.css';

function App() {
  const [code, setCode] = useState('print("Hello, World!")');
  const [output, setOutput] = useState('');
  const [aiFeedback, setAiFeedback] = useState('');
  const [exercise, setExercise] = useState(null);
  const [activeTab, setActiveTab] = useState('exercise');
  const [solutionFeedback, setSolutionFeedback] = useState(null);

  // Automatically generate an exercise on first load
  useEffect(() => {
    handleGenerateExercise();
  }, []);

  const clearOutput = () => {
    setOutput('');
    setAiFeedback('');
    setSolutionFeedback(null);
  }

  const handleRunCode = async () => {
    clearOutput();
    setActiveTab('output'); // Switch to output tab on run
    const response = await fetch('http://localhost:8000/api/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code }),
    });
    const data = await response.json();
    setOutput(data.output);
    setAiFeedback(data.ai_feedback);
  };

  const handleGenerateExercise = async () => {
    clearOutput();
    setExercise(null);
    setActiveTab('exercise'); // Switch to exercise tab
    const response = await fetch('http://localhost:8000/api/generate-exercise');
    const data = await response.json();
    setExercise(data);

    const functionNameMatch = data.description?.match(/`(\w+)\(.*\)`/);
    if (functionNameMatch && functionNameMatch[1]) {
      setCode(`def ${functionNameMatch[1]}():\n  # Your code here\n  pass\n`);
    } else {
      setCode(`# Solve the exercise here`);
    }
  };

  const handleCheckSolution = async () => {
    if (!exercise) return;
    clearOutput();
    setActiveTab('output');
    const response = await fetch('http://localhost:8000/api/check-solution', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, exercise }),
    });
    const data = await response.json();
    setSolutionFeedback(data);
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
            <Button variant="secondary" onClick={handleGenerateExercise}>New Exercise</Button>
            <Button variant="secondary" onClick={handleCheckSolution} disabled={!exercise}>Check Solution</Button>
            <Button variant="primary" onClick={handleRunCode}>Run Code</Button>
          </div>
        </div>
        <div className="right-panel">
          <Tabs activeKey={activeTab} onSelect={(k) => setActiveTab(k)} id="output-tabs" className="mb-3">
            <Tab eventKey="exercise" title="Exercise">
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
            </Tab>
            <Tab eventKey="output" title="Output">
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
              <pre className="output-pre">{output}</pre>
              {aiFeedback && (
                <Card className="mt-3">
                  <Card.Header as="h5">🤖 AI Tutor Feedback</Card.Header>
                  <Card.Body>
                    <Card.Text>{aiFeedback}</Card.Text>
                  </Card.Body>
                </Card>
              )}
            </Tab>
          </Tabs>
        </div>
      </div>
    </div>
  );
}

export default App;
