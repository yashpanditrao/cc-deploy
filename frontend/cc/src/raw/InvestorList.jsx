import React, { useState, useEffect } from 'react'
import supabase from '../supabaseConfig'
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Link } from 'react-router-dom'

const InvestorList = () => {
  const [investors, setInvestors] = useState([])
  const [filteredInvestors, setFilteredInvestors] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedStage, setSelectedStage] = useState('all')
  const [selectedSector, setSelectedSector] = useState('all')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchInvestors()
  }, [])

  const fetchInvestors = async () => {
    try {
      const { data, error } = await supabase
        .from('investors')
        .select('*')
        .order('name')

      if (error) throw error
      setInvestors(data)
      setFilteredInvestors(data)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching investors:', error)
      setLoading(false)
    }
  }

  useEffect(() => {
    let result = investors

    // Filter by search term
    if (searchTerm) {
      result = result.filter(investor =>
        investor.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        investor.description?.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    // Filter by stage
    if (selectedStage && selectedStage !== 'all') {
      result = result.filter(investor =>
        investor.stage_focus?.includes(selectedStage)
      )
    }

    // Filter by sector
    if (selectedSector && selectedSector !== 'all') {
      result = result.filter(investor =>
        investor.sector_focus?.includes(selectedSector)
      )
    }

    setFilteredInvestors(result)
  }, [searchTerm, selectedStage, selectedSector, investors])

  const generateSlug = (name) => {
    return name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '')
  }

  if (loading) {
    return <div className="flex justify-center items-center h-screen">Loading...</div>
  }

  return (
    <div className="container mx-auto py-8">
      <div className="space-y-4 mb-8">
        <h1 className="text-3xl font-bold">Venture Firms</h1>
        
        <div className="flex gap-4 flex-wrap">
          <Input
            placeholder="Search investors..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="max-w-xs"
          />
          
          <Select onValueChange={setSelectedStage} value={selectedStage}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Stage Focus" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Stages</SelectItem>
              <SelectItem value="Pre-Seed">Pre-Seed</SelectItem>
              <SelectItem value="Seed">Seed</SelectItem>
              <SelectItem value="Series A">Series A</SelectItem>
              <SelectItem value="Series B">Series B</SelectItem>
              <SelectItem value="Series C">Series C</SelectItem>
              <SelectItem value="Series D">Series D</SelectItem>
              <SelectItem value="Series E">Series E</SelectItem>
            </SelectContent>
          </Select>

          <Select onValueChange={setSelectedSector} value={selectedSector}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Sector Focus" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Sectors</SelectItem>
              <SelectItem value="SaaS">SaaS</SelectItem>
              <SelectItem value="Consumer">Consumer</SelectItem>
              <SelectItem value="Supply Chain">Supply Chain</SelectItem>
              <SelectItem value="Healthcare">Healthcare</SelectItem>
              <SelectItem value="Finance">Finance</SelectItem>
              <SelectItem value="Energy">Energy</SelectItem>
              <SelectItem value="Education">Education</SelectItem>
              <SelectItem value="Deep Tech">Deep Tech</SelectItem>
              <SelectItem value="Other">Other</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredInvestors.map((investor) => (
          <Link 
            key={investor.id} 
            to={`/investor/${generateSlug(investor.name)}`}
            className="block hover:no-underline"
          >
            <Card className="h-full hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-center gap-4">
                  {investor.logo_url && (
                    <img 
                      src={investor.logo_url} 
                      alt={`${investor.name} logo`}
                      className="w-12 h-12 object-contain"
                    />
                  )}
                  <div>
                    <CardTitle>{investor.name}</CardTitle>
                    <CardDescription className="line-clamp-2">
                      {investor.description}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex flex-wrap gap-2">
                    {investor.stage_focus?.map((stage, index) => (
                      <Badge key={index} variant="secondary">{stage}</Badge>
                    ))}
                  </div>
                  <div className="text-sm text-gray-500">
                    <p>Ticket Size: {investor.ticket_size}</p>
                    <p>Portfolio Companies: {investor.total_portfolio}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}

export default InvestorList
