import React, { useState, useEffect } from 'react';
import { ChatInput } from '@/components/chat/ChatInput';
import { ChatMessages } from '@/components/chat/ChatMessages';
import { SearchResults } from '@/components/chat/SearchResults';
import { SearchOptions } from '@/components/chat/SearchOptions';
import { useChat } from '@/hooks/useChat';
import { Card } from '@/components/ui/card';
import { Loader2, MessageSquare, Search, Settings2, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

const ChatPage = () => {
  const [searchResults, setSearchResults] = useState([]);
  const [searchType] = useState('profile');
  const [roleFilter, setRoleFilter] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const { messages, sendMessage, isLoading } = useChat();

  const handleSearch = async (query) => {
    try {
      setIsSearching(true);
      const response = await fetch('https://cc-deploy-8heq.onrender.com/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          search_type: 'profile',
          num_results: 5,
          ...(roleFilter && { role_filter: roleFilter })
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Search failed: ${response.statusText}`);
      }
      
      const data = await response.json();
      setSearchResults(data.results || []);
    } catch (error) {
      console.error('Search error:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const getPlaceholderText = () => {
    return roleFilter 
      ? `Search for ${roleFilter.toLowerCase()} profiles...`
      : "Search for profiles by skills, experience, or background...";
  };

  return (
    <div className="h-[calc(100vh-4rem)] container mx-auto py-4 px-2">
      <div className="flex gap-4 h-full max-h-full">
        {/* Main Chat Area */}
        <Card className="flex-1 flex flex-col overflow-hidden bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="shrink-0 p-4 border-b flex items-center justify-between bg-background">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-primary/10">
                <Sparkles className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h1 className="text-xl font-semibold">AI Assistant</h1>
                <p className="text-sm text-muted-foreground">Search for talented professionals</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {roleFilter && (
                <Badge variant="secondary" className="hidden md:inline-flex">
                  {roleFilter}
                </Badge>
              )}
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-9 w-9"
                    title="Search Options"
                  >
                    <Settings2 className="h-5 w-5" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-80" align="end">
                  <div className="space-y-4">
                    <div className="flex items-center gap-2">
                      <div className="p-2 rounded-lg bg-primary/10">
                        <Search className="w-4 h-4 text-primary" />
                      </div>
                      <h2 className="font-semibold">Search Options</h2>
                    </div>
                    <SearchOptions 
                      searchType={searchType}
                      roleFilter={roleFilter}
                      onRoleFilterChange={setRoleFilter}
                    />
                  </div>
                </PopoverContent>
              </Popover>
            </div>
          </div>

          <ScrollArea className="flex-1 px-4 py-6">
            <div className="max-w-3xl mx-auto">
              <ChatMessages 
                messages={messages} 
                onSendMessage={(message) => {
                  sendMessage(message, searchType);
                  handleSearch(message);
                }}
              />
            </div>
          </ScrollArea>

          <div className="shrink-0 p-4 border-t bg-background">
            <div className="max-w-3xl mx-auto">
              <ChatInput 
                onSend={(message) => {
                  sendMessage(message, searchType);
                  handleSearch(message);
                }}
                isLoading={isLoading || isSearching}
                placeholder={getPlaceholderText()}
              />
              {(isLoading || isSearching) && (
                <p className="text-sm text-muted-foreground mt-2 text-center">
                  {isSearching ? "Searching..." : "Processing your request..."}
                </p>
              )}
            </div>
          </div>
        </Card>

        {/* Search Results Sidebar */}
        <Card className="w-80 flex-shrink-0 flex flex-col overflow-hidden bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 hidden md:flex">
          <div className="shrink-0 p-4 border-b bg-background">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-primary/10">
                <Search className="w-5 h-5 text-primary" />
              </div>
              <h2 className="text-lg font-semibold">Search Results</h2>
            </div>
          </div>
          
          <ScrollArea className="flex-1">
            <div className="p-4">
              {isSearching ? (
                <div className="flex flex-col items-center justify-center h-24 gap-2">
                  <Loader2 className="h-6 w-6 animate-spin text-primary" />
                  <p className="text-sm text-muted-foreground">Searching for matches...</p>
                </div>
              ) : (
                <SearchResults 
                  results={searchResults} 
                  type={searchType}
                />
              )}
            </div>
          </ScrollArea>
        </Card>
      </div>
    </div>
  );
};

export default ChatPage;