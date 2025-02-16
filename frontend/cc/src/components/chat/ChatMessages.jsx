import React from 'react';
import { cn } from '@/lib/utils';
import { Bot, User, Search, Sparkles, MessageSquare } from 'lucide-react';
import { Button } from '@/components/ui/button';

const MessageSuggestions = ({ onSuggestionClick }) => {
  const suggestions = [
    { 
      icon: <Search className="w-4 h-4" />, 
      text: "Find AR/VR engineers with Unity experience",
      type: 'profile'
    },
    { 
      icon: <MessageSquare className="w-4 h-4" />, 
      text: "Search for full-stack developers with React experience",
      type: 'profile'
    },
    { 
      icon: <Sparkles className="w-4 h-4" />, 
      text: "Find product managers with startup experience",
      type: 'profile'
    }
  ];

  return (
    <div className="grid gap-2 mt-6">
      <p className="text-sm text-muted-foreground">Try asking:</p>
      <div className="grid gap-2">
        {suggestions.map((suggestion, index) => (
          <Button
            key={index}
            variant="ghost"
            className="flex items-center gap-2 text-sm p-2 h-auto font-normal justify-start hover:bg-muted"
            onClick={() => onSuggestionClick(suggestion.text)}
          >
            {suggestion.icon}
            <span>{suggestion.text}</span>
          </Button>
        ))}
      </div>
    </div>
  );
};

export const ChatMessages = ({ messages, onSendMessage }) => {
  if (!messages.length) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-8">
        <div className="p-3 rounded-xl bg-primary/10 mb-4">
          <Bot className="h-12 w-12 text-primary" />
        </div>
        <h3 className="text-xl font-semibold mb-2">Welcome to FounderHive Assistant</h3>
        <p className="text-sm text-muted-foreground max-w-sm mb-4">
          I can help you find and learn about profiles and companies in our database. Just ask me anything!
        </p>
        <MessageSuggestions onSuggestionClick={onSendMessage} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {messages.map((message, index) => (
        <div
          key={index}
          className={cn(
            "flex items-start gap-3 text-sm",
            message.type === 'user' ? "justify-end" : "justify-start"
          )}
        >
          {message.type !== 'user' && (
            <div className="flex-shrink-0 rounded-full h-8 w-8 bg-primary/10 flex items-center justify-center">
              <Bot className="h-5 w-5 text-primary" />
            </div>
          )}
          
          <div
            className={cn(
              "rounded-lg px-4 py-2.5 max-w-[85%] break-words shadow-sm",
              message.type === 'user'
                ? "bg-primary text-primary-foreground"
                : "bg-muted/50 hover:bg-muted/80 transition-colors"
            )}
          >
            {message.content}
          </div>

          {message.type === 'user' && (
            <div className="flex-shrink-0 rounded-full h-8 w-8 bg-primary flex items-center justify-center shadow-sm">
              <User className="h-5 w-5 text-primary-foreground" />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}; 