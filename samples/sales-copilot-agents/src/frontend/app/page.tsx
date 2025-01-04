'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { useToast } from "@/components/ui/use-toast"
import { Toaster } from "@/components/ui/toaster"
import { Quicksand } from 'next/font/google'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  FileText, 
  MessageSquare,
  StickyNote,
  Wand2,
  Loader2,
  User,
  Building,
  Mail,
  Clock
} from 'lucide-react'
import { TooltipProvider, TooltipRoot, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip"

const quicksand = Quicksand({ subsets: ['latin'] })

// Add API URL from environment variable
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface ReportData {
  crmInfo?: {
    name: string;
    department: string;
    email: string;
    tenure: string;
  };
  customerStory?: {
    background: string;
    keyPoints: string[];
    sentiment: string;
    actionItems: string[];
  };
  engineeringFeedback?: {
    feedback: string;
    actionItems: string[];
    priority: string;
  };
  progress?: {
    crmInfo: boolean;
    customerStory: boolean;
    engineeringFeedback: boolean;
  };
}

// Update the color constants for better reuse
const colors = {
  primary: '#00AFFF', // Bright blue
  secondary: '#4ECDC4', // Turquoise
  accent: '#0090FF', // Darker blue for hover
  background: '#111111',
  cardBg: '#1f1f1f',
  inputBg: '#2a2a2a',
}

export default function RapidReportGenerator() {
  const [customerFeedback, setCustomerFeedback] = useState('')
  const [customerContext, setCustomerContext] = useState('')
  const [salesNotes, setSalesNotes] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [reportData, setReportData] = useState<ReportData | null>(null)
  const [progress, setProgress] = useState({
    crmInfo: false,
    customerStory: false,
    engineeringFeedback: false
  })
  const { toast } = useToast()

  const handleGenerateReport = async () => {
    if (!customerFeedback.trim()) {
      toast({
        title: "Missing Information",
        description: "Please provide the Teams meeting transcript.",
        variant: "destructive"
      })
      return
    }

    setIsGenerating(true)
    setProgress({
      crmInfo: false,
      customerStory: false,
      engineeringFeedback: false
    })
    setReportData(null)

    try {
      toast({
        title: "Generating Report",
        description: "Your report is being synthesized...",
      })

      // Base64 encode the inputs
      const requestData = {
        transcript: btoa(unescape(encodeURIComponent(customerFeedback))), // Handle UTF-8
        notes: customerContext ? btoa(unescape(encodeURIComponent(customerContext))) : "",
        crmId: salesNotes || "" // CRM ID doesn't need encoding
      }

      // Make the API call
      const response = await fetch(`${API_URL}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `API error: ${response.statusText}`)
      }

      const result = await response.json()

      // Update progress and report data based on API response
      setProgress({
        crmInfo: true,
        customerStory: true,
        engineeringFeedback: true
      })

      setReportData({
        crmInfo: {
          name: result.crm_info.name || 'N/A',
          department: result.crm_info.department || 'N/A',
          email: result.crm_info.email || 'N/A',
          tenure: result.crm_info.tenure || 'N/A'
        },
        customerStory: {
          background: result.customer_story.customer_background || '',
          keyPoints: result.customer_story.key_points || [],
          sentiment: result.customer_story.sentiment || 'neutral',
          actionItems: result.customer_story.action_items || []
        },
        engineeringFeedback: {
          feedback: result.engineering_feedback.feedback || '',
          actionItems: result.engineering_feedback.action_items || [],
          priority: result.engineering_feedback.priority || 'medium'
        }
      })

      toast({
        title: "Report Generated",
        description: "Your report has been successfully generated!",
        variant: "success"
      })
    } catch (error) {
      console.error('Error generating report:', error)
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to generate report. Please try again.",
        variant: "destructive"
      })
    } finally {
      setIsGenerating(false)
    }
  }

  const isFormValid = customerFeedback.trim().length > 0

  const getTooltipMessage = () => {
    if (!customerFeedback.trim()) {
      return "Please provide the Teams meeting transcript to generate a report"
    }
    if (isGenerating) {
      return "Report generation in progress..."
    }
    return "Generate a report from the provided information"
  }

  return (
    <TooltipProvider delayDuration={200}>
      <div className={`min-h-screen bg-[#111111] text-white p-8 ${quicksand.className}`}>
        {/* Header with updated SVG colors */}
        <div className="flex flex-col items-center mb-8">
          <div className="flex items-center gap-3 mb-2">
            <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
              {/* Core module */}
              <rect x="12" y="12" width="16" height="16" fill="#1f1f1f" stroke="#00AFFF" strokeWidth="2"/>
              {/* Extension connectors */}
              <path d="M28 20H36" stroke="#00AFFF" strokeWidth="2"/>
              <path d="M4 20H12" stroke="#00AFFF" strokeWidth="2"/>
              <path d="M20 28V36" stroke="#00AFFF" strokeWidth="2"/>
              <path d="M20 4V12" stroke="#00AFFF" strokeWidth="2"/>
              {/* Extension modules */}
              <circle cx="36" cy="20" r="3" fill="#4ECDC4"/>
              <circle cx="4" cy="20" r="3" fill="#4ECDC4"/>
              <circle cx="20" cy="36" r="3" fill="#4ECDC4"/>
              <circle cx="20" cy="4" r="3" fill="#4ECDC4"/>
              {/* Pulse dots */}
              <circle cx="28" cy="20" r="1" fill="#4ECDC4"/>
              <circle cx="12" cy="20" r="1" fill="#4ECDC4"/>
              <circle cx="20" cy="28" r="1" fill="#4ECDC4"/>
              <circle cx="20" cy="12" r="1" fill="#4ECDC4"/>
            </svg>
            <h1 className="text-4xl font-bold text-[#00AFFF] tracking-wide">Microsoft 365 Copilot for Sales extensions</h1>
          </div>
          <p className="text-center text-gray-400">Synthesize customer feedback into actionable insights</p>
        </div>

        {/* Main content */}
        <div className="flex gap-8 max-w-[1800px] mx-auto">
          {/* Left side forms with updated colors */}
          <div className="w-1/2 space-y-6">
            <Card className="bg-[#1f1f1f] border-[#00AFFF] hover:shadow-[0_0_10px_rgba(0,175,255,0.3)] transition-shadow duration-300">
              <CardHeader>
                <CardTitle className="text-[#00AFFF] flex items-center gap-2">
                  <FileText className="h-6 w-6" />
                  Metadata
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Input
                  placeholder="CRM references (Dynamics 365, Salesforce, etc.), pipeline stage ..."
                  className="bg-[#2a2a2a] border-[#00AFFF] focus:ring-[#00AFFF] text-white placeholder:text-gray-400"
                  value={salesNotes}
                  onChange={(e) => setSalesNotes(e.target.value)}
                />
              </CardContent>
            </Card>
            
            <Card className="bg-[#1f1f1f] border-[#00AFFF] hover:shadow-[0_0_10px_rgba(0,175,255,0.3)] transition-shadow duration-300">
              <CardHeader>
                <CardTitle className="text-[#00AFFF] flex items-center gap-2">
                  <MessageSquare className="h-6 w-6" />
                  Meeting transcripts (Teams, Zoom etc.)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Textarea
                  placeholder="Paste or type raw transcript here..."
                  className="min-h-[150px] bg-[#2a2a2a] border-[#00AFFF] focus:ring-[#00AFFF] text-white placeholder:text-gray-400"
                  value={customerFeedback}
                  onChange={(e) => setCustomerFeedback(e.target.value)}
                />
              </CardContent>
            </Card>

            <Card className="bg-[#1f1f1f] border-[#00AFFF] hover:shadow-[0_0_10px_rgba(0,175,255,0.3)] transition-shadow duration-300">
              <CardHeader>
                <CardTitle className="text-[#00AFFF] flex items-center gap-2">
                  <StickyNote className="h-6 w-6" />
                  Additional notes
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Textarea
                  placeholder="Use bullet points or free-form text..."
                  className="min-h-[150px] bg-[#2a2a2a] border-[#00AFFF] focus:ring-[#00AFFF] text-white placeholder:text-gray-400"
                  value={customerContext}
                  onChange={(e) => setCustomerContext(e.target.value)}
                />
              </CardContent>
            </Card>

            <div className="flex justify-center mt-8">
              <TooltipRoot>
                <TooltipTrigger asChild>
                  <span className="inline-block w-2/3"> {/* Increased width */}
                    <Button
                      onClick={handleGenerateReport}
                      disabled={isGenerating || !isFormValid}
                      className="w-full bg-[#00AFFF] text-white hover:bg-[#0090FF] transition-all duration-300 text-xl px-8 py-4 rounded-lg shadow-lg hover:shadow-[0_0_30px_rgba(0,175,255,0.5)] flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed font-semibold"
                    >
                      {isGenerating ? (
                        <Loader2 className="h-6 w-6 animate-spin" />
                      ) : (
                        <Wand2 className="h-6 w-6" />
                      )}
                      {isGenerating ? 'Generating...' : 'Generate Report'}
                    </Button>
                  </span>
                </TooltipTrigger>
                <TooltipContent side="top" align="center">
                  <p>{getTooltipMessage()}</p>
                </TooltipContent>
              </TooltipRoot>
            </div>
          </div>

          {/* Right side results with updated colors */}
          <div className="w-1/2">
            <AnimatePresence>
              {isGenerating && !reportData && (
                <div className="space-y-6">
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="flex flex-col items-center justify-center min-h-[200px] bg-[#1f1f1f] rounded-lg border border-[#00AFFF] p-6"
                  >
                    <Loader2 className="h-8 w-8 animate-spin text-[#00AFFF] mb-4" />
                    <div className="space-y-2 text-center">
                      <h3 className="text-lg font-semibold text-[#00AFFF]">Generating Report</h3>
                      <div className="space-y-1 text-gray-400">
                        <p className={progress.crmInfo ? "text-[#00AFFF]" : ""}>
                          {progress.crmInfo ? "✓" : "○"} Retrieving customer information...
                        </p>
                        <p className={progress.customerStory ? "text-[#00AFFF]" : ""}>
                          {progress.customerStory ? "✓" : "○"} Analyzing customer story...
                        </p>
                        <p className={progress.engineeringFeedback ? "text-[#00AFFF]" : ""}>
                          {progress.engineeringFeedback ? "✓" : "○"} Generating engineering feedback...
                        </p>
                      </div>
                    </div>
                  </motion.div>
                </div>
              )}
              {reportData && (
                <div className="space-y-6">
                  {/* CRM Info */}
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.5 }}
                  >
                    <Card className="bg-[#1f1f1f] border-[#00AFFF]">
                      <CardHeader>
                        <CardTitle className="text-[#00AFFF] flex items-center gap-2">
                          <User className="h-6 w-6" />
                          Customer Information
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="flex items-center gap-2 text-gray-300">
                          <User className="h-4 w-4" />
                          <span>{reportData.crmInfo?.name}</span>
                        </div>
                        <div className="flex items-center gap-2 text-gray-300">
                          <Building className="h-4 w-4" />
                          <span>{reportData.crmInfo?.department}</span>
                        </div>
                        <div className="flex items-center gap-2 text-gray-300">
                          <Mail className="h-4 w-4" />
                          <span>{reportData.crmInfo?.email}</span>
                        </div>
                        <div className="flex items-center gap-2 text-gray-300">
                          <Clock className="h-4 w-4" />
                          <span>{reportData.crmInfo?.tenure}</span>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>

                  {/* Customer Story */}
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.5, delay: 0.2 }}
                  >
                    <Card className="bg-[#1f1f1f] border-[#00AFFF]">
                      <CardHeader>
                        <CardTitle className="text-[#00AFFF]">Customer Story Analysis</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="space-y-2">
                          <h3 className="text-[#00AFFF] font-semibold">Background</h3>
                          <p className="text-gray-300">{reportData.customerStory?.background}</p>
                        </div>
                        <div className="space-y-2">
                          <h3 className="text-[#00AFFF] font-semibold">Key Points</h3>
                          <ul className="list-disc list-inside text-gray-300">
                            {reportData.customerStory?.keyPoints.map((point, i) => (
                              <li key={i}>{point}</li>
                            ))}
                          </ul>
                        </div>
                        <div className="space-y-2">
                          <h3 className="text-[#00AFFF] font-semibold">Action Items</h3>
                          <ul className="list-disc list-inside text-gray-300">
                            {reportData.customerStory?.actionItems.map((item, i) => (
                              <li key={i}>{item}</li>
                            ))}
                          </ul>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>

                  {/* Engineering Feedback */}
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.5, delay: 0.4 }}
                  >
                    <Card className="bg-[#1f1f1f] border-[#00AFFF]">
                      <CardHeader>
                        <CardTitle className="text-[#00AFFF]">Engineering Feedback</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="space-y-2">
                          <h3 className="text-[#00AFFF] font-semibold">Analysis</h3>
                          <p className="text-gray-300">{reportData.engineeringFeedback?.feedback}</p>
                        </div>
                        <div className="space-y-2">
                          <h3 className="text-[#00AFFF] font-semibold">Action Items</h3>
                          <ul className="list-disc list-inside text-gray-300">
                            {reportData.engineeringFeedback?.actionItems.map((item, i) => (
                              <li key={i}>{item}</li>
                            ))}
                          </ul>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-[#00AFFF] font-semibold">Priority:</span>
                          <span className="text-gray-300">{reportData.engineeringFeedback?.priority}</span>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                </div>
              )}
            </AnimatePresence>
          </div>
        </div>
        <Toaster />
      </div>
    </TooltipProvider>
  )
}
