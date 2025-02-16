import React from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import InvestorList from './raw/InvestorList'
import InvestorDetail from './raw/InvestorDetail'
import ChatPage from '@/pages/chat/ChatPage'
import ProfilePage from '@/pages/profile/ProfilePage'
import { ThemeProvider } from "./components/theme-provider"
import Data from './raw/Data'

function App() {
  return (
    <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
      <Router>
        <div className="min-h-screen bg-background text-foreground">
          {/* Navigation */}
          <nav className="sticky top-0 z-40 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="container mx-auto px-4">
              <div className="flex h-16 items-center">
                <div className="flex">
                  <div className="flex items-center">
                    <Link to="/" className="text-xl font-bold hover:text-primary transition-colors">
                      FounderHive
                    </Link>
                  </div>
                  <div className="ml-6 flex space-x-8">
                    <Link
                      to="/"
                      className="inline-flex items-center px-1 pt-1 text-muted-foreground hover:text-foreground transition-colors"
                    >
                      Investor Search
                    </Link>
                    <Link
                      to="/chat"
                      className="inline-flex items-center px-1 pt-1 text-muted-foreground hover:text-foreground transition-colors"
                    >
                      Co-Founder Search
                    </Link>
                    <Link
                      to="/analyze"
                      className="inline-flex items-center px-1 pt-1 text-muted-foreground hover:text-foreground transition-colors"
                    >
                     Fundraising Assistant
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </nav>

          {/* Main Content */}
          <main className="container mx-auto px-4">
            <Routes>
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/" element={<InvestorList />} />
              <Route path="/investor/:slug" element={<InvestorDetail />} />
              <Route path="/analyze" element={<Data />} />
              <Route path="/profile/:id" element={<ProfilePage />} />
            </Routes>
          </main>
        </div>
      </Router>
    </ThemeProvider>
  )
}

export default App
