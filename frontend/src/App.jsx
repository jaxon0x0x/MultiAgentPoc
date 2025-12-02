import { useState } from 'react'
import './App.css'
import LiveKitModal from './components/LiveKitModal';

// if false do not show livekit modal
function App() {
  const [showSupport, setShowSupport] = useState(false);

//if click sos button show livekit modal
  const handleSupportClick = () => {
    setShowSupport(true);
  };
  // const help_log = () => {
  //   console.log("Help button clicked");
  // };

  const [backendMessage, setBackendMessage] = useState(null);
  const handleBackendClick = async () => {
  try {
    const res = await fetch("/api/ping"); // albo "/ping" zależnie od proxy
    const data = await res.json();
    setBackendMessage(data.message);
  } catch (err) {
    console.error(err);
    setBackendMessage("Error talking to backend");
  }
};
  return (
    <div className="app">
      {!showSupport && (
        <main className="main-content">
          <button className="sos-button" onClick={handleSupportClick}>
            SOS
          </button>
          <p className="sos-helper-text">Press in case of emergency</p>

          <button onClick={handleBackendClick}>
            Check backend
          </button>
            {backendMessage && (
              <p className="backend-message">{backendMessage}</p>
            )}
        </main>
      )}

      {showSupport && <LiveKitModal setShowSupport={setShowSupport} />}
    </div>
  );
}

export default App;
