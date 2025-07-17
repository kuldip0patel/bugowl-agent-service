import React, { useState, useRef, useEffect } from 'react';

const LiveStream = () => {
  const [token, setToken] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [frame, setFrame] = useState(null);
  const websocket = useRef(null);

  const handleConnect = () => {
    if (token && !isConnected) {
      const wsUri = `ws://localhost:8020/agent/LiveStreaming/?token=${token}`;
      websocket.current = new WebSocket(wsUri);

      websocket.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
      };

      websocket.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'browser_frame' && data.frame) {
          setFrame(`data:image/jpeg;base64,${data.frame}`);
        }
      };

      websocket.current.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        setFrame(null);
      };

      websocket.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
        setFrame(null);
      };
    }
  };

  const handleDisconnect = () => {
    if (websocket.current) {
      websocket.current.close();
    }
  };

  useEffect(() => {
    return () => {
      if (websocket.current) {
        websocket.current.close();
      }
    };
  }, []);

  return (
    <div>
      <h2>Live Stream</h2>
      <div>
        <input
          type="text"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          placeholder="Enter token"
          disabled={isConnected}
        />
        {!isConnected ? (
          <button onClick={handleConnect} disabled={!token}>
            Connect
          </button>
        ) : (
          <button onClick={handleDisconnect}>Disconnect</button>
        )}
      </div>
      <div style={{
        border: '1px solid #ccc',
        boxShadow: '0 4px 8px 0 rgba(0,0,0,0.2)',
        marginTop: '20px',
        marginLeft: '20px',
        marginBottom: '20px',
        maxWidth: '80%',
        overflow: 'hidden',
        backgroundColor: '#000'
      }}>
        {isConnected && frame ? (
          <img src={frame} alt="Live stream" style={{ width: '100%', display: 'block' }} />
        ) : (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            height: '480px',
            color: '#fff'
          }}>
            <p>{isConnected ? 'Waiting for frames...' : 'Disconnected'}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default LiveStream;
