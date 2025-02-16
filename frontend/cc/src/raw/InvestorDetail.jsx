import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import supabase from '../supabaseConfig'
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ArrowLeft } from 'lucide-react'

const InvestorDetail = () => {
  const { slug } = useParams()
  const [investor, setInvestor] = useState(null)
  const [loading, setLoading] = useState(true)
  const [vcProfiles, setVcProfiles] = useState(null)
  const [findingVC, setFindingVC] = useState(false)

  useEffect(() => {
    fetchInvestor()
  }, [slug])

  const fetchInvestor = async () => {
    try {
      const { data, error } = await supabase
        .from('investors')
        .select('*')
      
      if (error) throw error

      // Find the investor by matching the slug
      const foundInvestor = data.find(inv => 
        inv.name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '') === slug
      )

      setInvestor(foundInvestor)
      if (foundInvestor?.profiles) {
        setVcProfiles(foundInvestor.profiles)
      }
      setLoading(false)
    } catch (error) {
      console.error('Error fetching investor:', error)
      setLoading(false)
    }
  }

  const findVC = async () => {
    try {
      setFindingVC(true)
      const response = await fetch('https://cc-deploy-1.onrender.com/find-vc', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: investor.name
        }),
      })
      const data = await response.json()
      setVcProfiles(data.profiles)
      console.log(data.profiles)
    } catch (error) {
      console.error('Error finding VC:', error)
    } finally {
      setFindingVC(false)
    }
  }

  if (loading) {
    return <div className="flex justify-center items-center h-screen">Loading...</div>
  }

  if (!investor) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Investor not found</h1>
          <Link to="/">
            <Button>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Investors
            </Button>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-8">
      <Link to="/">
        <Button variant="ghost" className="mb-6">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Investors
        </Button>
      </Link>

      <Card className="max-w-4xl mx-auto">
        <CardHeader>
          <div className="flex items-center gap-6">
            {investor.logo_url && (
              <img 
                src={investor.logo_url} 
                alt={`${investor.name} logo`}
                className="w-24 h-24 object-contain"
              />
            )}
            <div>
              <CardTitle className="text-3xl">{investor.name}</CardTitle>
              <CardDescription className="text-lg mt-2">
                {investor.description}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold mb-2">Investment Focus</h3>
              <div className="flex flex-wrap gap-2">
                {investor.stage_focus && investor.stage_focus.map((stage, index) => (
                  <Badge key={index} variant="secondary">{stage}</Badge>
                ))}
              </div>
            </div>

            <div>
              <h3 className="text-lg font-semibold mb-2">Sector Focus</h3>
              <div className="flex flex-wrap gap-2">
                {investor.sector_focus && investor.sector_focus.map((sector, index) => (
                  <Badge key={index}>{sector}</Badge>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h3 className="text-lg font-semibold mb-2">Investment Details</h3>
                <div className="space-y-2">
                  <p><span className="font-medium">Ticket Size:</span> {investor.ticket_size}</p>
                  <p><span className="font-medium">Total Portfolio:</span> {investor.total_portfolio} companies</p>
                  <p><span className="font-medium">Current Fund:</span> {investor.current_fund_corpus}</p>
                  <p><span className="font-medium">Total Funds Under Management:</span> {investor.total_fund_corpus}</p>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold mb-2">Contact Information</h3>
                <p className="whitespace-pre-wrap">{investor.best_way_to_contact}</p>
              </div>
            </div>

            <div>
              {!vcProfiles && (
                <Button onClick={findVC} disabled={findingVC}>
                  {findingVC ? 'Finding VC...' : `Find VC from ${investor.name}`}
                </Button>
              )}
              {vcProfiles && vcProfiles.length > 0 && (
                <div className="mt-4">
                  <h3 className="text-lg font-semibold mb-2">VC Profiles</h3>
                  {vcProfiles.map((profile, index) => (
                    <div key={index} className="mb-2">
                      <a href={profile.link} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                        {profile.link}
                      </a>
                      <p className="text-sm text-gray-600">{profile.snippet}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {investor.pitch_now && (
              <div className="mt-4">
                <a href={investor.pitch_now} target="_blank" rel="noopener noreferrer">
                  <Button className="w-full">Pitch Now</Button>
                </a>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default InvestorDetail 