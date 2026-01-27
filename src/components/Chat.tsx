import React, { useState, useRef, useEffect } from 'react';

// Types for our chat messages
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  image?: string; // Base64 encoded image
  timestamp: Date;
}

interface ChatProps {
  // In a real Tauri app, this would likely be an async function invoking a Tauri command
  // or an HTTP request to the sidecar.
  onSendMessage?: (message: string, image?: string) => Promise<string>;
  blackboardContent?: string;
}

export const Chat: React.FC<ChatProps> = ({ onSendMessage, blackboardContent }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingState, setLoadingState] = useState<'idle' | 'checking_vocab' | 'typing'>('idle');
  const [activeTab, setActiveTab] = useState<'chat' | 'blackboard'>('chat');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (activeTab === 'chat') {
      scrollToBottom();
    }
  }, [messages, loadingState, selectedImage, activeTab]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if ((!inputValue.trim() && !selectedImage) || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue.trim(),
      image: selectedImage || undefined,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setSelectedImage(null);
    setIsLoading(true);
    
    // Simulate the "Think -> Tool -> Response" flow for UI demonstration
    setLoadingState('checking_vocab');

    try {
      // Mocking the delay and response if no handler is provided
      let responseContent = "";
      
      if (onSendMessage) {
        // If we had a real backend connection, we might get intermediate events.
        // For now, we'll simulate the "Checking vocabulary..." delay.
        await new Promise(resolve => setTimeout(resolve, 1500)); 
        setLoadingState('typing');
        
        responseContent = await onSendMessage(userMessage.content, userMessage.image);
      } else {
        // Simulation for development/preview
        await new Promise(resolve => setTimeout(resolve, 1500)); // Time for "Checking vocabulary"
        setLoadingState('typing');
        await new Promise(resolve => setTimeout(resolve, 1500)); // Time for "Typing"
        responseContent = "こんにちは！ (This is a mock response. Connect the backend to see real output.)";
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: responseContent,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Failed to send message:", error);
      // Handle error state in UI
    } finally {
      setIsLoading(false);
      setLoadingState('idle');
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      processFile(file);
    }
  };

  const processFile = (file: File) => {
    if (!file.type.startsWith('image/')) return;
    
    const reader = new FileReader();
    reader.onloadend = () => {
      setSelectedImage(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    const items = e.clipboardData.items;
    for (let i = 0; i < items.length; i++) {
      if (items[i].type.indexOf('image') !== -1) {
        const file = items[i].getAsFile();
        if (file) {
          processFile(file);
          e.preventDefault(); // Prevent pasting the file name or binary data as text
        }
      }
    }
  };

  return (
    <div className="flex flex-col h-screen max-w-2xl mx-auto bg-gray-50 border-x border-gray-200">
      {/* Header */}
      <div className="bg-white p-4 border-b border-gray-200 shadow-sm flex items-center justify-between sticky top-0 z-10">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Nihongo Dojo</h1>
          <p className="text-xs text-green-600 font-medium flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-green-500"></span>
            Online
          </p>
        </div>
        
        {/* Toggle Switch */}
        <div className="flex bg-gray-100 rounded-lg p-1">
            <button
                onClick={() => setActiveTab('chat')}
                className={`px-3 py-1 text-sm font-medium rounded-md transition-all ${
                    activeTab === 'chat' 
                    ? 'bg-white text-gray-800 shadow-sm' 
                    : 'text-gray-500 hover:text-gray-700'
                }`}
            >
                Chat
            </button>
            <button
                onClick={() => setActiveTab('blackboard')}
                className={`px-3 py-1 text-sm font-medium rounded-md transition-all ${
                    activeTab === 'blackboard' 
                    ? 'bg-white text-gray-800 shadow-sm' 
                    : 'text-gray-500 hover:text-gray-700'
                }`}
            >
                Blackboard
            </button>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 relative">
        {activeTab === 'chat' ? (
            <>
                {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full text-gray-400 text-center">
                    <p className="mb-2">はじまりましょう！</p>
                    <p className="text-sm">Start chatting to practice your Japanese.</p>
                </div>
                )}

                {messages.map((msg) => (
                <div
                    key={msg.id}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                    <div
                    className={`max-w-[80%] rounded-2xl p-2 shadow-sm ${
                        msg.role === 'user'
                        ? 'bg-blue-600 text-white rounded-br-none'
                        : 'bg-white text-gray-800 border border-gray-100 rounded-bl-none'
                    }`}
                    >
                    {msg.image && (
                        <img 
                        src={msg.image} 
                        alt="User attachment" 
                        className="rounded-lg max-h-60 mb-2 object-cover w-full" 
                        />
                    )}
                    <div className="px-2">
                        <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</p>
                        <span 
                        className={`text-[10px] block text-right mt-1 ${
                            msg.role === 'user' ? 'text-blue-200' : 'text-gray-400'
                        }`}
                        >
                        {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                    </div>
                    </div>
                </div>
                ))}

                {/* Loading / Typing Indicators */}
                {isLoading && (
                <div className="flex justify-start">
                    <div className="bg-white border border-gray-100 rounded-2xl rounded-bl-none px-4 py-3 shadow-sm flex items-center gap-2">
                    {loadingState === 'checking_vocab' ? (
                        <div className="flex items-center gap-2 text-xs text-indigo-600 font-medium">
                        <svg className="animate-spin h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                        Checking vocabulary...
                        </div>
                    ) : (
                        <div className="flex gap-1">
                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
                        </div>
                    )}
                    </div>
                </div>
                )}
                
                <div ref={messagesEndRef} />
            </>
        ) : (
            // Blackboard View
            <div className="h-full bg-white rounded-lg shadow-sm border border-gray-200 p-6 overflow-y-auto">
                 <h2 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2 border-b pb-2">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-indigo-600"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
                    Study Notes
                 </h2>
                 {blackboardContent ? (
                     <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap">
                         {blackboardContent}
                     </div>
                 ) : (
                     <div className="flex flex-col items-center justify-center h-40 text-gray-400 italic">
                         <p>No notes on the blackboard yet.</p>
                     </div>
                 )}
            </div>
        )}
      </div>

      {/* Input Area - Only show in Chat mode */}
      {activeTab === 'chat' && (
          <div className="bg-white p-4 border-t border-gray-200">
            {selectedImage && (
            <div className="mb-2 relative inline-block">
                <img src={selectedImage} alt="Preview" className="h-20 rounded-lg border border-gray-300 shadow-sm" />
                <button 
                    onClick={() => setSelectedImage(null)}
                    className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 shadow-md hover:bg-red-600"
                >
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
            </div>
            )}
            <form onSubmit={handleSendMessage} className="flex items-center gap-2">
            {/* File Input (Hidden) */}
            <input 
                type="file" 
                accept="image/*" 
                ref={fileInputRef} 
                onChange={handleFileSelect} 
                className="hidden" 
            />
            
            {/* Attachment Button */}
            <button 
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="text-gray-400 hover:text-gray-600 p-2 rounded-full hover:bg-gray-100 transition-colors"
                title="Attach image"
            >
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>
            </button>

            <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onPaste={handlePaste}
                placeholder="Type a message..."
                className="flex-1 bg-gray-100 border-0 rounded-full px-4 py-3 text-gray-900 focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all outline-none"
                disabled={isLoading}
            />
            <button
                type="submit"
                disabled={(!inputValue.trim() && !selectedImage) || isLoading}
                className="bg-blue-600 text-white p-3 rounded-full hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
            </button>
            </form>
        </div>
      )}
    </div>
  );
};

export default Chat;
