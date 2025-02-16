import { useState } from "react";

export const useChat = () => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async (content, searchType = "profile") => {
    setIsLoading(true);

    // Add user message
    setMessages((prev) => [...prev, { type: "user", content }]);

    try {
      // Add system response
      const systemMessage =
        searchType === "profile"
          ? `Searching for profiles matching: "${content}"`
          : `Searching for companies matching: "${content}"`;

      setMessages((prev) => [
        ...prev,
        {
          type: "system",
          content: systemMessage,
        },
      ]);
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) => [
        ...prev,
        {
          type: "system",
          content: "Sorry, there was an error processing your request.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return {
    messages,
    sendMessage,
    isLoading,
  };
};
