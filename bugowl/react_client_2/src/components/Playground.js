import React, { useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import './Playground.css';
import TaskEditor from './TaskEditor';

const Playground = () => {
  // WebSocket connection states
  const [token, setToken] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [webSocket, setWebSocket] = useState(null);
  
  // Frame data states
  const [frameData, setFrameData] = useState('');
  const [currentUrl, setCurrentUrl] = useState('');
  const [metaData, setMetaData] = useState({
    job_uuid: '',
    job_status: '',
    case_uuid: '',
    case_status: '',
    task_uuid: '',
    task_status: ''
  });

  // Task management states
  const [tasks, setTasks] = useState([]);
  const [selectedTaskUuid, setSelectedTaskUuid] = useState(null);

  // WebSocket message handler
  const handleWebSocketMessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      console.log('Received data:', data);
      
      if (data.type === 'browser_frame') {
        setFrameData(data.frame);
        setCurrentUrl(data.current_url || '');
        setMetaData({
          job_uuid: data.job_uuid || '',
          job_status: data.job_status || '',
          case_uuid: data.case_uuid || '',
          case_status: data.case_status || '',
          task_uuid: data.task_uuid || '',
          task_status: data.task_status || ''
        });
      }

      // Update task status based on received data
      const updatedTasks = tasks.map(task => {
        if (task.uuid === data.task_uuid) {
          return { ...task, status: data.task_status };
        }
        return task;
      });
      setTasks(updatedTasks);
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  };

  // Connect to WebSocket
  const connectWebSocket = () => {
    if (!token) {
      alert('Please enter a token');
      return;
    }

    try {
      // Use token as query parameter in the WebSocket URL
      const wsUrl = `ws://localhost:8020/agent/PlayGround/?token=${token}`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('WebSocket connection established');
        setIsConnected(true);
        setWebSocket(ws);
      };

      ws.onmessage = handleWebSocketMessage;

      ws.onclose = () => {
        console.log('WebSocket connection closed');
        setIsConnected(false);
        setWebSocket(null);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };
    } catch (error) {
      console.error('Error connecting to WebSocket:', error);
    }
  };

  // Disconnect from WebSocket
  const disconnectWebSocket = () => {
    if (webSocket) {
      webSocket.close();
      setIsConnected(false);
      setWebSocket(null);
    }
  };

  // Send command to WebSocket
  const sendCommand = (command, data = {}) => {
    if (!webSocket || webSocket.readyState !== WebSocket.OPEN) {
      alert('WebSocket is not connected');
      return;
    }

    const payload = {
      COMMAND: command,
      ...data
    };

    console.log(`Sending ${command} command:`, payload);
    webSocket.send(JSON.stringify(payload));
  };

  // Command handlers
  const handleLoadTasks = () => {
    if (tasks.length === 0) {
      alert('Please add at least one task');
      return;
    }
    
    sendCommand('C2S_LOAD_TASK', {
      ALL_TASK_DATA: tasks.map(task => ({
        uuid: task.uuid,
        title: task.title,
        data: null
      }))
    });
  };

  const handleExecuteAllTasks = () => {
    if (tasks.length === 0) {
      alert('Please add at least one task');
      return;
    }

    sendCommand('C2S_RUN_ALL_TASKS', {
      ALL_TASK_DATA: tasks.map(task => ({
        uuid: task.uuid,
        title: task.title,
        data: null
      }))
    });
  };

  const handleExecuteTask = () => {
    if (!selectedTaskUuid) {
      alert('Please select a task to execute');
      return;
    }

    sendCommand('C2S_RUN_TASK', {
      TASK_UUID: selectedTaskUuid,
      ALL_TASK_DATA: tasks.map(task => ({
        uuid: task.uuid,
        title: task.title,
        data: null
      }))
    });
  };

  const handleAddTask = () => {
    const newTask = {
      uuid: uuidv4(),
      title: `Task ${tasks.length + 1}`,
      data: null,
      status: 'Pending' // Add a default status
    };
    
    setTasks((prevTasks) => [...prevTasks, newTask]); // Use functional update to avoid overwriting
    if (!selectedTaskUuid) {
      setSelectedTaskUuid(newTask.uuid);
    }
  };

  const handleUpdateTask = (updatedTask) => {
    setTasks(tasks.map(task => 
      task.uuid === updatedTask.uuid ? updatedTask : task
    ));
  };

  const handleDeleteTask = (taskUuid) => {
    setTasks(tasks.filter(task => task.uuid !== taskUuid));
    if (selectedTaskUuid === taskUuid) {
      setSelectedTaskUuid(tasks.length > 1 ? tasks[0].uuid : null);
    }
  };

  return (
    <div className="playground-container">
      <div className="connection-panel">
        <div className="token-input">
          <input 
            type="text"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="Enter token"
            disabled={isConnected}
          />
          {!isConnected ? (
            <button onClick={connectWebSocket}>Connect</button>
          ) : (
            <button onClick={disconnectWebSocket}>Disconnect</button>
          )}
        </div>
      </div>

      <div className="main-content">
        <div className="stream-container">
          <div className="url-display">
            {currentUrl && <div>Current URL: {currentUrl}</div>}
          </div>
          <div className="frame-display">
            {frameData ? (
              <img src={`data:image/png;base64,${frameData}`} alt="Browser frame" />
            ) : (
              <div className="no-frame">No frame data available</div>
            )}
          </div>
        </div>
        
        <div className="metadata-panel">
          <h3>Session Information</h3>
          <div className="metadata-item">
            <span>Job UUID:</span> {metaData.job_uuid}
          </div>
          <div className="metadata-item">
            <span>Job Status:</span> {metaData.job_status}
          </div>
          <div className="metadata-item">
            <span>Case UUID:</span> {metaData.case_uuid}
          </div>
          <div className="metadata-item">
            <span>Case Status:</span> {metaData.case_status}
          </div>
          <div className="metadata-item">
            <span>Task UUID:</span> {metaData.task_uuid}
          </div>
          <div className="metadata-item">
            <span>Task Status:</span> {metaData.task_status}
          </div>
        </div>
      </div>

      <div className="control-panel">
        <div className="command-buttons">
          <button onClick={handleLoadTasks} disabled={!isConnected}>C2S_LOAD_TASK</button>
          <button onClick={handleExecuteAllTasks} disabled={!isConnected}>C2S_EXECUTE_ALL_TASKS</button>
          <button onClick={handleExecuteTask} disabled={!isConnected || !selectedTaskUuid}>C2S_EXECUTE_TASK</button>
          <button onClick={() => sendCommand('C2S_STOP')} disabled={!isConnected}>C2S_STOP</button>
          <button onClick={() => sendCommand('C2S_PAUSE')} disabled={!isConnected}>C2S_PAUSE</button>
          <button onClick={() => sendCommand('C2S_RESUME')} disabled={!isConnected}>C2S_RESUME</button>
          <button onClick={() => sendCommand('C2S_RESTART')} disabled={!isConnected}>C2S_RESTART</button>
        </div>
      </div>

      <div className="task-editor-panel">
        <div className="task-editor-header">
          <h3>Task Management</h3>
          <button onClick={handleAddTask}>Add Task</button>
        </div>
        
        <div className="task-list">
          {tasks.length === 0 ? (
            <div className="no-tasks">No tasks added. Click "Add Task" to create a new task.</div>
          ) : (
            tasks.map(task => (
              <TaskEditor 
                key={task.uuid}
                task={task}
                isSelected={task.uuid === selectedTaskUuid}
                onSelect={() => setSelectedTaskUuid(task.uuid)}
                onUpdate={handleUpdateTask}
                onDelete={() => handleDeleteTask(task.uuid)}
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default Playground;
