import { useState, useCallback, useEffect, useRef } from "react";
import { LiveKitRoom, RoomAudioRenderer } from "@livekit/components-react";
import axios from "axios";
import "@livekit/components-styles";
import SimpleVoiceAssistant from "./SimpleVoiceAssistant";

// LiveKit modal component where we store the state for the session
const LiveKitModal = ({ setShowSupport }) => {
  const [isSubmittingName, setIsSubmittingName] = useState(true);
  const [name, setName] = useState("");
  const [token, setToken] = useState(null);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const [sharingPhoto, setSharingPhoto] = useState(false);
  const [uploadedPhoto, setUploadedPhoto] = useState(null);
  const [sharedPhoto, setSharedPhoto] = useState(null);
  const [mapData, setMapData] = useState(null);
  const [mapLoading, setMapLoading] = useState(false);
  const [photoAnalysis, setPhotoAnalysis] = useState(null);
  const fileInputRef = useRef(null);

  // Function to get token from backend
  const getToken = useCallback(async (userName) => {
    try {
      const response = await fetch(`/api/getToken?name=${encodeURIComponent(userName)}`);
      const token = await response.text();
      setToken(token);
      setIsSubmittingName(false);
    } catch (error) {
      console.error(error);
    }
  }, []);

  // Function to handle photo upload
  const handlePhotoUpload = async (file) => {
    if (!file) return;
    setUploadingPhoto(true);
    try {
      const formData = new FormData();
      formData.append("photo", file);
      const response = await axios.post("/api/upload-photo", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      const { url } = response.data;
      setPhotoAnalysis(response.data.analysis);
      setUploadedPhoto(url);
    } catch (error) {
      console.error("Failed to upload image", error);
    } finally {
      setUploadingPhoto(false);
    }
  };

  // Function to handle sharing photo with first Agent
  const handleSharePhoto = async () => {
    if (!uploadedPhoto) return;
    setSharingPhoto(true);
    try {
      await axios.post("/api/data", { topic: "image-share", url: uploadedPhoto });
      setSharedPhoto(uploadedPhoto);
    } catch (error) {
      console.error("Failed to share image", error);
    } finally {
      setSharingPhoto(false);
    }
  };

    // Fetch map data on component mount
  useEffect(() => {
    const fetchMap = async () => {
      setMapLoading(true);
      try {
        const response = await fetch("/api/map");
        if (!response.ok) {
          throw new Error("Map request failed");
        }
        const data = await response.json();
        setMapData(data);
      } catch (error) {
        console.error("Failed to load map", error);
      } finally {
        setMapLoading(false);
      }
    };
    fetchMap();
  }, []);

  const connected = Boolean(token && !isSubmittingName);

  const handleNameSubmit = (e) => {
    e.preventDefault();
    if (name.trim()) {
      getToken(name);
    }
  };

  return (
    <div className={`modal-overlay ${connected ? "connected" : ""}`}>
      <div className={`modal-content ${connected ? "connected" : ""}`}>
        <button className="close-button" onClick={() => setShowSupport(false)}>
          &times;
        </button>
        <div className="support-room">
          {isSubmittingName ? (
            <form onSubmit={handleNameSubmit} className="name-form">
              <h2>Enter your name to connect with support</h2>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Your name"
                required
              />
              <button type="submit">Connect</button>
              <button
                type="button"
                className="cancel-button"
                onClick={() => setShowSupport(false)}
              >
                Cancel
              </button>
            </form>
          ) : token ? (
            <LiveKitRoom
              serverUrl={import.meta.env.VITE_LIVEKIT_URL}
              token={token}
              connect={true}
              video={false}
              audio={true}
              onDisconnected={() => {
                setShowSupport(false);
                setIsSubmittingName(true);
              }}
            >
              <div className="modal-grid">
                <section className="voice-pane">
                  <div className="voice-header">
                    <h3>Voice Assistant</h3>
                  </div>
                  <RoomAudioRenderer />
                  <SimpleVoiceAssistant />
                </section>
                <section className="map-pane">
                  <div className="map-header">
                    <h3>Live Location</h3>
                    {mapData?.latlng && (
                      <p className="map-info">
                        Lat {mapData.latlng[0].toFixed(4)}, Lng {mapData.latlng[1].toFixed(4)}
                      </p>
                    )}
                  </div>
                  <div className="map-wrapper">
                    {mapLoading ? (
                      <div className="map-loading">Loading map...</div>
                    ) : mapData?.map_url ? (
                      <iframe
                        title="Current location"
                        src={mapData.map_url}
                        className="map-frame"
                      />
                    ) : (
                      <div className="map-error">Location unavailable.</div>
                    )}
                  </div>
                  <div className="map-photo-section">
                    <div className="map-photo-actions">
                      <input
                        type="file"
                        accept="image/*"
                        ref={fileInputRef}
                        hidden
                        onChange={(e) => handlePhotoUpload(e.target.files[0])}
                      />
                      <button
                        type="button"
                        className="upload-button"
                        onClick={() => fileInputRef.current.click()}
                        disabled={uploadingPhoto}
                      >
                        {uploadingPhoto ? "Uploading..." : "Upload Photo"}
                      </button>
                      <button
                        type="button"
                        className="share-button"
                        onClick={handleSharePhoto}
                        disabled={!uploadedPhoto || sharingPhoto}
                      >
                        {sharingPhoto ? "Sharing..." : "Share Photo"}
                      </button>
                    </div>
                    <div className="map-photo-preview">
                      {uploadedPhoto ? (
                        <img src={uploadedPhoto} alt="Uploaded" />
                      ) : (
                        <p>Upload an image of the incident.</p>
                      )}
                    </div>
                    {photoAnalysis && (
                      <div className="analysis-note">
                        <h4>Incident note</h4>
                        <p>{photoAnalysis}</p>
                      </div>
                    )}
                    {sharedPhoto && (
                      <div className="shared-photo-display">
                        <h4>Shared with first responders</h4>
                        <img src={sharedPhoto} alt="Shared" />
                        <p>Realtime photo has been delivered.</p>
                      </div>
                    )}
                  </div>
                </section>
              </div>
            </LiveKitRoom>
          ) : null}
        </div>
      </div>
    </div>
  );
};

export default LiveKitModal;
