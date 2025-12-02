import {
  useVoiceAssistant,
  BarVisualizer,
  VoiceAssistantControlBar,
  useTrackTranscription,
  useLocalParticipant,
} from "@livekit/components-react";
import { Track } from "livekit-client";
import { useEffect, useState } from "react";
import "./SimpleVoiceAssistant.css";
// Simple voice assistant showing agent
const Message = ({ type, text }) => (
  <div className="message">
    <strong className={`message-${type}`}>{type === "agent" ? "Agent:" : "You:"}</strong>
    <span className="message-text">{text}</span>
  </div>
);

// Return state of assistant, audio visualizer, control bar, and transcript
const SimpleVoiceAssistant = () => {
  const { state, audioTrack, agentTranscriptions } = useVoiceAssistant();
  const localParticipant = useLocalParticipant();
  const { segments: userTranscriptions } = useTrackTranscription({
    publication: localParticipant.microphoneTrack,
    source: Track.Source.Microphone,
    participant: localParticipant.localParticipant,
  });

  const [messages, setMessages] = useState([]);

  useEffect(() => {
    const allMessages = [
      ...(agentTranscriptions?.map((t) => ({ ...t, type: "agent" })) ?? []),
      ...(userTranscriptions?.map((t) => ({ ...t, type: "user" })) ?? []),
    ].sort((a, b) => a.firstReceivedTime - b.firstReceivedTime);
    setMessages(allMessages);
  }, [agentTranscriptions, userTranscriptions]);

  return (
    <div className="voice-assistant-container">
      <div className="transcript-container">
        {messages.length ? (
          messages.map((msg, index) => <Message key={msg.id || index} type={msg.type} text={msg.text} />)
        ) : (
          <p className="no-messages">Waiting for transcripts...</p>
        )}
      </div>
      <div className="voice-controls">
        <div className="visualizer-container">
          <BarVisualizer state={state} barCount={7} trackRef={audioTrack} />
        </div>
        <VoiceAssistantControlBar />
      </div>
    </div>
  );
};

export default SimpleVoiceAssistant;