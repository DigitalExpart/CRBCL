import React, { useState, useRef, useEffect } from "react";
import { api } from "@/api";
import { Send, Bot, User, Loader2, Sparkles, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import ReactMarkdown from "react-markdown";
import PageHeader from "@/components/shared/PageHeader";

const SUGGESTED_PROMPTS = [
  "How many active cases do we have?",
  "Summarize today's upcoming appointments",
  "What programs have the highest enrollment?",
  "Draft a case note for a family visit",
  "What is our total active funding?",
  "List all critical or urgent cases",
  "What are common referral sources?",
  "Help me write a progress report",
];

export default function AskRedBear() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const gatherContext = async () => {
    const [cases, clients, programs, funding, appointments] = await Promise.all([
      api.entities.Case.list("-created_date", 20),
      api.entities.Client.list("-created_date", 20),
      api.entities.Program.list("-created_date", 20),
      api.entities.FundingGrant.list("-created_date", 20),
      api.entities.Appointment.list("-date", 10),
    ]);

    const activeCases = cases.filter(c => c.status !== "Closed");
    const criticalCases = cases.filter(c => c.priority === "Critical" || c.priority === "Urgent");
    const activeClients = clients.filter(c => c.status === "Active");
    const activePrograms = programs.filter(p => p.status === "Active");
    const activeFunding = funding.filter(f => f.status === "Active" || f.status === "Approved");
    const scheduledAppts = appointments.filter(a => a.status === "Scheduled");

    return `CRBCL DATA CONTEXT:
- Total Cases: ${cases.length}, Active: ${activeCases.length}, Critical/Urgent: ${criticalCases.length}
- Case Types: ${[...new Set(cases.map(c => c.case_type))].join(", ")}
- Critical Cases: ${criticalCases.map(c => `${c.title} (${c.case_type}, assigned to ${c.assigned_worker_name || "unassigned"})`).join("; ") || "None"}
- Total Clients: ${clients.length}, Active: ${activeClients.length}
- Active Programs: ${activePrograms.map(p => `${p.name} (${p.category}, ${p.enrolled_count}/${p.capacity} enrolled)`).join("; ") || "None"}
- Active Funding: ${activeFunding.map(f => `${f.name} from ${f.funder}: $${f.amount?.toLocaleString()}, spent $${(f.amount_spent || 0).toLocaleString()}`).join("; ") || "None"}
- Total Active Funding: $${activeFunding.reduce((s, f) => s + (f.amount || 0), 0).toLocaleString()}
- Upcoming Appointments: ${scheduledAppts.map(a => `${a.title} on ${a.date} at ${a.time || "TBD"} with ${a.client_name || "—"}`).join("; ") || "None"}
- Recent Cases: ${activeCases.slice(0, 5).map(c => `${c.title} (${c.status}, ${c.priority} priority, ${c.case_type})`).join("; ")}`;
  };

  const handleSend = async (text) => {
    const msg = text || input.trim();
    if (!msg || loading) return;

    const userMessage = { role: "user", content: msg };
    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    const context = await gatherContext();

    const response = await api.integrations.Core.InvokeLLM({
      prompt: `You are "Ask Red Bear", the AI assistant for Chief Red Bear Children's Lodge (CRBCL), an Indigenous child and family services organization in Saskatchewan, Canada.

You help staff with:
- Answering questions about cases, clients, programs, and funding
- Drafting case notes, reports, and emails
- Providing insights and analytics
- Recommending actions based on data
- Compliance and policy guidance

Be warm, professional, culturally sensitive, and helpful. Use the data context provided. Format responses with clear headers, bullet points, and summaries where appropriate.

${context}

CONVERSATION HISTORY:
${messages.map(m => `${m.role === "user" ? "Staff" : "Red Bear"}: ${m.content}`).join("\n")}

Staff: ${msg}

Respond helpfully as Ask Red Bear:`,
      model: "claude_sonnet_4_6",
    });

    setMessages(prev => [...prev, { role: "assistant", content: response }]);
    setLoading(false);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] lg:h-[calc(100vh-4rem)]">
      <PageHeader
        title="Ask Red Bear"
        subtitle="Your AI assistant for case management, reporting, and insights"
        actions={
          messages.length > 0 && (
            <Button variant="outline" size="sm" onClick={() => setMessages([])}>
              <RotateCcw className="w-4 h-4 mr-1" /> New Chat
            </Button>
          )
        }
      />

      {/* Chat Area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto scrollbar-thin space-y-4 pb-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            <div className="w-20 h-20 rounded-2xl bg-primary/10 flex items-center justify-center mb-6">
              <Sparkles className="w-9 h-9 text-primary" />
            </div>
            <h2 className="text-xl font-heading font-bold text-foreground mb-2">Welcome to Ask Red Bear</h2>
            <p className="text-sm text-muted-foreground max-w-md mb-8">
              I can help you look up case information, draft notes, analyze program data, and provide organizational insights.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-lg w-full">
              {SUGGESTED_PROMPTS.map((prompt, i) => (
                <button
                  key={i}
                  onClick={() => handleSend(prompt)}
                  className="text-left p-3 rounded-lg border border-border bg-card hover:bg-muted/50 text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}>
              {msg.role === "assistant" && (
                <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0 mt-1">
                  <Bot className="w-4 h-4 text-primary" />
                </div>
              )}
              <div className={`max-w-[80%] rounded-xl px-4 py-3 ${
                msg.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-card border border-border"
              }`}>
                {msg.role === "user" ? (
                  <p className="text-sm">{msg.content}</p>
                ) : (
                  <ReactMarkdown className="text-sm prose prose-sm max-w-none prose-headings:font-heading prose-headings:text-foreground prose-p:text-foreground prose-li:text-foreground prose-strong:text-foreground">
                    {msg.content}
                  </ReactMarkdown>
                )}
              </div>
              {msg.role === "user" && (
                <div className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center flex-shrink-0 mt-1">
                  <User className="w-4 h-4 text-muted-foreground" />
                </div>
              )}
            </div>
          ))
        )}
        {loading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
              <Bot className="w-4 h-4 text-primary" />
            </div>
            <div className="bg-card border border-border rounded-xl px-4 py-3">
              <Loader2 className="w-4 h-4 animate-spin text-primary" />
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t border-border pt-4 mt-auto">
        <div className="flex gap-2 items-end">
          <Textarea
            ref={inputRef}
            rows={1}
            placeholder="Ask Red Bear anything…"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            className="min-h-[44px] max-h-32 resize-none"
          />
          <Button onClick={() => handleSend()} disabled={!input.trim() || loading} className="h-11 w-11 p-0 flex-shrink-0">
            <Send className="w-4 h-4" />
          </Button>
        </div>
        <p className="text-[10px] text-muted-foreground mt-2 text-center">
          Ask Red Bear uses AI to assist you. Always verify critical information.
        </p>
      </div>
    </div>
  );
}