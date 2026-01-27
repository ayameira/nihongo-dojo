import { useState } from 'react';
import Chat from './components/Chat';

function App() {
  const [blackboardContent, setBlackboardContent] = useState<string>("");

  const handleSendMessage = async (message: string, image?: string) => {
    // In the future, this will communicate with the backend via Tauri commands or sidecar
    console.log("User sent:", message);
    if (image) {
      console.log("Image attached (length):", image.length);
    }
    
    // Simulating backend response for now
    await new Promise(resolve => setTimeout(resolve, 3000));
    const imageAck = image ? " I also received your image!" : "";

    // Mock update to blackboard if user asks to "write" something
    if (message.toLowerCase().includes("blackboard")) {
        setBlackboardContent(prev => prev + "\n- New note added: " + message);
    }

    return `You said: "${message}".${imageAck} I checked the database and... (Real logic coming soon)`;
  };

  return (
    <Chat 
      onSendMessage={handleSendMessage} 
      blackboardContent={blackboardContent}
    />
  );
}

export default App;
