import { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Loader2 } from "lucide-react";

const API_BASE_URL = 'https://cc-deploy-1.onrender.com';

export default function Data() {
  const [loading, setLoading] = useState({
    analysis: false,
    queries: false,
    competitors: false,
    vcFirms: false
  });
  const [data, setData] = useState({
    analysis: null,
    queries: null,
    competitors: null,
    vcFirms: null
  });
  const [error, setError] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [url, setUrl] = useState('');
  const [stage, setStage] = useState('Seed');
  const [comparingStates, setComparingStates] = useState({});
  const comparisonRef = useRef(null);
  
  // Chat state
  const [messages, setMessages] = useState([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [conversationState, setConversationState] = useState(null);
  const [companyInfo, setCompanyInfo] = useState(null);
  const messagesEndRef = useRef(null);
  const scrollAreaRef = useRef(null);
  const [chatLoading, setChatLoading] = useState(false);

  const scrollToBottom = () => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    }
  };

  useEffect(() => {
    if (messages.length > 0) {
      scrollToBottom();
    }
  }, [messages]);

  // Start conversation when component mounts
  useEffect(() => {
    startConversation();
  }, []);

  const startConversation = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: '', conversation_state: null })
      });
      if (!response.ok) throw new Error('Failed to start conversation');
      const data = await response.json();
      setMessages([{ type: 'assistant', content: data.response }]);
      setConversationState(data.conversation_state);
    } catch (err) {
      setError(err.message);
    }
  };

  const sendMessage = async () => {
    if (!currentMessage.trim() || chatLoading) return;

    // Add user message to chat
    const userMessage = currentMessage.trim();
    setMessages(prev => [...prev, { type: 'user', content: userMessage }]);
    setCurrentMessage('');
    setChatLoading(true);

    try {
      // Add typing indicator
      setMessages(prev => [...prev, { type: 'assistant', content: null }]);

      // Send message with current company info
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: companyInfo ? `${userMessage}|||${JSON.stringify(companyInfo)}` : userMessage,
          conversation_state: conversationState
        })
      });
      
      if (!response.ok) throw new Error('Failed to send message');
      const data = await response.json();
      
      // Replace typing indicator with actual response
      setMessages(prev => [
        ...prev.slice(0, -1),
        { type: 'assistant', content: data.response }
      ]);
      setConversationState(data.conversation_state);
      setCompanyInfo(data.company_info);

      // If conversation is complete, analyze the company
      if (data.is_complete && data.company_info) {
        await analyzeCompanyInfo(data.company_info);
      }
    } catch (err) {
      setError(err.message);
      // Remove typing indicator if there was an error
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setChatLoading(false);
    }
  };

  const analyzeCompanyInfo = async (info) => {
    setError(null);
    setComparison(null);
    
    // Reset all data
    setData({
      analysis: null,
      queries: null,
      competitors: null,
      vcFirms: null
    });

    // Step 1: Analyze company info
    setLoading(prev => ({ ...prev, analysis: true }));
    try {
      const analysisResponse = await fetch(`${API_BASE_URL}/analyze-company-info`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(info)
      });
      if (!analysisResponse.ok) throw new Error('Company analysis failed');
      const analysisData = await analysisResponse.json();
      setData(prev => ({ ...prev, analysis: analysisData }));

      // Step 2: Generate queries
      setLoading(prev => ({ ...prev, queries: true }));
      const queriesResponse = await fetch(`${API_BASE_URL}/generate-queries`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ summary: analysisData.website_analysis.summary })
      });
      if (!queriesResponse.ok) throw new Error('Query generation failed');
      const queriesData = await queriesResponse.json();
      setData(prev => ({ ...prev, queries: queriesData.queries }));

      // Step 3: Search competitors
      setLoading(prev => ({ ...prev, competitors: true }));
      const competitorsResponse = await fetch(`${API_BASE_URL}/search-competitors`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          summary: analysisData.website_analysis.summary,
          queries: queriesData.queries
        })
      });
      if (!competitorsResponse.ok) throw new Error('Competitor search failed');
      const competitorsData = await competitorsResponse.json();
      setData(prev => ({ ...prev, competitors: competitorsData.competitors }));

      // Step 4: Get VC firms
      setLoading(prev => ({ ...prev, vcFirms: true }));
      const vcResponse = await fetch(`${API_BASE_URL}/vc-firms`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sectors: analysisData.website_analysis.sectors,
          stage: info.current_stage
        })
      });
      if (!vcResponse.ok) throw new Error('VC firms search failed');
      const vcData = await vcResponse.json();
      setData(prev => ({ ...prev, vcFirms: vcData.firms }));

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading({
        analysis: false,
        queries: false,
        competitors: false,
        vcFirms: false
      });
    }
  };

  const compareWithCompetitor = async (competitorUrl) => {
    try {
      setComparingStates(prev => ({ ...prev, [competitorUrl]: true }));
      const response = await fetch(`${API_BASE_URL}/compare`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url1: url,
          url2: competitorUrl
        })
      });
      if (!response.ok) throw new Error('Comparison failed');
      const comparisonData = await response.json();
      setComparison(comparisonData);
      // Scroll to comparison results after they load
      setTimeout(() => {
        comparisonRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } catch (err) {
      setError(err.message);
    } finally {
      setComparingStates(prev => ({ ...prev, [competitorUrl]: false }));
    }
  };

  const analyzeWebsite = async () => {
    if (!url) return;
    setError(null);
    setComparison(null);
    
    // Reset all data
    setData({
      analysis: null,
      queries: null,
      competitors: null,
      vcFirms: null
    });

    // Step 1: Analyze website
    setLoading(prev => ({ ...prev, analysis: true }));
    try {
      const analysisResponse = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });
      if (!analysisResponse.ok) throw new Error('Website analysis failed');
      const analysisData = await analysisResponse.json();
      setData(prev => ({ ...prev, analysis: analysisData }));

      // Step 2: Generate queries
      setLoading(prev => ({ ...prev, queries: true }));
      const queriesResponse = await fetch(`${API_BASE_URL}/generate-queries`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });
      if (!queriesResponse.ok) throw new Error('Query generation failed');
      const queriesData = await queriesResponse.json();
      setData(prev => ({ ...prev, queries: queriesData.queries }));

      // Step 3: Search competitors
      setLoading(prev => ({ ...prev, competitors: true }));
      const competitorsResponse = await fetch(`${API_BASE_URL}/search-competitors`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          summary: analysisData.website_analysis.summary,
          queries: queriesData.queries
        })
      });
      if (!competitorsResponse.ok) throw new Error('Competitor search failed');
      const competitorsData = await competitorsResponse.json();
      setData(prev => ({ ...prev, competitors: competitorsData.competitors }));

      // Step 4: Get VC firms
      setLoading(prev => ({ ...prev, vcFirms: true }));
      const vcResponse = await fetch(`${API_BASE_URL}/vc-firms`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sectors: analysisData.website_analysis.sectors,
          stage: stage
        })
      });
      if (!vcResponse.ok) throw new Error('VC firms search failed');
      const vcData = await vcResponse.json();
      setData(prev => ({ ...prev, vcFirms: vcData.firms }));

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading({
        analysis: false,
        queries: false,
        competitors: false,
        vcFirms: false
      });
    }
  };

  return (
    <div className="container mx-auto p-4 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Fundraising Assistant</CardTitle>
          <CardDescription>Analyze your startup and find relevant investors</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="chat" className="space-y-4">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="chat">Chat with AI</TabsTrigger>
              <TabsTrigger value="website">Enter Website URL</TabsTrigger>
            </TabsList>

            <TabsContent value="chat" className="space-y-4">
              <div className="space-y-4">
                <ScrollArea ref={scrollAreaRef} className="h-[400px] p-4 border rounded-lg">
                  <div className="space-y-4">
                    {messages.map((message, index) => (
                      <div
                        key={index}
                        className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[80%] p-3 rounded-lg ${
                            message.type === 'user'
                              ? 'bg-primary text-primary-foreground ml-4'
                              : 'bg-muted'
                          }`}
                        >
                          {message.content === null ? (
                            <div className="flex items-center gap-2">
                              <Loader2 className="h-4 w-4 animate-spin" />
                              <span className="text-sm">Thinking...</span>
                            </div>
                          ) : (
                            message.content
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
                
                <div className="flex gap-2">
                  <Input
                    placeholder="Type your message..."
                    value={currentMessage}
                    onChange={(e) => setCurrentMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                    disabled={chatLoading}
                  />
                  <Button 
                    onClick={sendMessage} 
                    disabled={!currentMessage.trim() || chatLoading}
                  >
                    {chatLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      'Send'
                    )}
                  </Button>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="website" className="space-y-4">
              <div className="flex gap-4">
                <div className="flex-1">
                  <Input
                    placeholder="Enter your website URL..."
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                  />
                </div>
                <Select value={stage} onValueChange={setStage}>
                  <SelectTrigger className="w-[180px]">
                    <SelectValue placeholder="Select stage" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Pre-Seed">Pre-Seed</SelectItem>
                    <SelectItem value="Seed">Seed</SelectItem>
                    <SelectItem value="Series A">Series A</SelectItem>
                    <SelectItem value="Series B">Series B</SelectItem>
                  </SelectContent>
                </Select>
                <Button 
                  onClick={analyzeWebsite} 
                  disabled={Object.values(loading).some(Boolean)}
                >
                  {Object.values(loading).some(Boolean) ? (
                    <div className="flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Analyzing...</span>
                    </div>
                  ) : (
                    'Analyze'
                  )}
                </Button>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {error && (
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <p className="text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}
       {/* Market Analysis - Second */}
       {data.analysis?.market_analysis && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Market Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="whitespace-pre-wrap">{data.analysis.market_analysis.market_analysis}</p>
              {data.analysis.market_analysis.citations && (
                <div className="mt-4">
                  <h4 className="font-semibold mb-2">Sources</h4>
                  <ul className="list-disc list-inside text-sm text-muted-foreground">
                    {data.analysis.market_analysis.citations.map((citation, i) => (
                      <li key={i}>{citation}</li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>
        )}

      {/* Analysis Results Section */}
      <div className="space-y-6">
        {/* Company/Website Analysis - Always First */}
        {(loading.analysis || data.analysis) && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              {loading.analysis ? (
                <div className="space-y-4">
                  <Skeleton className="h-4 w-[250px]" />
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-3/4" />
                </div>
              ) : data.analysis && (
                <div className="grid gap-4">
                  <div>
                    <h3 className="font-semibold">Industry</h3>
                    <p>{data.analysis.website_analysis.industry}</p>
                  </div>
                  <div>
                    <h3 className="font-semibold">Solution</h3>
                    <p>{data.analysis.website_analysis.solution}</p>
                  </div>
                  <div>
                    <h3 className="font-semibold">Summary</h3>
                    <p>{data.analysis.website_analysis.summary}</p>
                  </div>
                  <div>
                    <h3 className="font-semibold">Sectors</h3>
                    <ul className="list-disc list-inside">
                      {data.analysis.website_analysis.sectors.map((sector, i) => (
                        <li key={i}>{sector}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}
         {/* Comparison Results */}
         {comparison && (
          <Card className="mb-6" ref={comparisonRef}>
            <CardHeader>
              <CardTitle>Comparison Results</CardTitle>
              <CardDescription>
                Comparing your company with competitor
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="relative overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="text-xs uppercase bg-muted">
                    <tr>
                      <th className="px-6 py-3">Aspect</th>
                      <th className="px-6 py-3">Your Company</th>
                      <th className="px-6 py-3">Competitor</th>
                    </tr>
                  </thead>
                  <tbody>
                    {comparison.comparison.comparison_table.map((row, i) => (
                      <tr key={i} className="border-b">
                        <td className="px-6 py-4 font-medium">{row.aspect}</td>
                        <td className="px-6 py-4">{row.company1}</td>
                        <td className="px-6 py-4">{row.company2}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="mt-4">
                <h4 className="font-semibold mb-2">Summary</h4>
                <p className="text-sm text-muted-foreground">
                  {comparison.comparison.summary}
                </p>
              </div>
            </CardContent>
          </Card>
        )}
       

        {/* Search Queries and Competitors - Last */}
        {(loading.competitors || data.competitors) && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Top Competitors</CardTitle>
            </CardHeader>
            <CardContent>
              {loading.competitors ? (
                <div className="space-y-4">
                  <Skeleton className="h-20 w-full" />
                  <Skeleton className="h-20 w-full" />
                  <Skeleton className="h-20 w-full" />
                </div>
              ) : (
                <div className="grid gap-4">
                  {data.competitors?.map((competitor, i) => (
                    <div key={i} className="p-4 rounded-lg border">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          {competitor.link && (
                            <img 
                              src={`https://www.google.com/s2/favicons?domain=${competitor.link}&sz=32`}
                              alt=""
                              className="w-8 h-8"
                            />
                          )}
                          <div>
                            <h3 className="font-semibold">{competitor.name}</h3>
                            {competitor.link && (
                              <a href={competitor.link} target="_blank" rel="noopener noreferrer" 
                                className="text-sm text-blue-500 hover:underline">
                                Visit Website
                              </a>
                            )}
                          </div>
                        </div>
                        {competitor.link && (
                          <Button 
                            variant="outline" 
                            onClick={() => compareWithCompetitor(competitor.link)}
                            disabled={comparingStates[competitor.link]}
                          >
                            {comparingStates[competitor.link] ? (
                              <div className="flex items-center gap-2">
                                <Loader2 className="h-4 w-4 animate-spin" />
                                <span>Comparing...</span>
                              </div>
                            ) : (
                              'Compare'
                            )}
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* VC Firms */}
        {(loading.vcFirms || data.vcFirms) && (
          <Card>
            <CardHeader>
              <CardTitle>Recommended VC Firms</CardTitle>
            </CardHeader>
            <CardContent>
              {loading.vcFirms ? (
                <div className="space-y-4">
                  <Skeleton className="h-24 w-full" />
                  <Skeleton className="h-24 w-full" />
                  <Skeleton className="h-24 w-full" />
                </div>
              ) : (
                <div className="grid gap-4">
                  {data.vcFirms?.map((firm, i) => (
                    <div key={i} className="p-4 rounded-lg border">
                      <div className="flex items-start gap-4">
                        {firm.logo_url && (
                          <img 
                            src={firm.logo_url} 
                            alt={`${firm.name} logo`}
                            className="w-12 h-12 object-contain"
                          />
                        )}
                        <div className="flex-1">
                          <h3 className="font-semibold">
                            <a 
                              href={`/investor/${firm.name.toLowerCase().replace(/\s+/g, '-')}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="hover:underline"
                            >
                              {firm.name}
                            </a>
                          </h3>
                          <p className="text-sm text-muted-foreground">Ticket Size: {firm.ticket_size}</p>
                          <p className="text-sm text-muted-foreground">Fund Size: {firm.current_fund_corpus}</p>
                          <div className="mt-2">
                            <h4 className="text-sm font-medium">Sectors:</h4>
                            <p className="text-sm text-muted-foreground">
                              {firm.sector_focus.join(', ')}
                            </p>
                          </div>
                          <div className="mt-1">
                            <h4 className="text-sm font-medium">Stages:</h4>
                            <p className="text-sm text-muted-foreground">
                              {firm.stage_focus.join(', ')}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}

       
      </div>
    </div>
  );
}
