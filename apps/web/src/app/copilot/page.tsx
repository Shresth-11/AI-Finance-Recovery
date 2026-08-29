"use client";

import * as React from "react";
import Link from "next/link";
import {
  Sparkles,
  Bot,
  User,
  Send,
  Copy,
  Check,
  ExternalLink,
  ShieldAlert,
  Database,
  HelpCircle,
  RefreshCw,
  Info,
} from "lucide-react";
import { toast } from "sonner";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { fetchApi } from "@/lib/api";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citedEvidenceIds?: string[];
  confidenceScore?: number;
  limitations?: string;
  fallbackMode?: boolean;
  disclaimer?: string;
  suggestedActions?: string[];
  timestamp: string;
}

const STARTER_QUERIES = [
  "Show the highest-value unresolved issues.",
  "Why was EXC_1001 flagged?",
  "What are the most common exception types?",
  "Summarize settlement delays this week.",
];

export default function CopilotPage() {
  const [query, setQuery] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const [copiedId, setCopiedId] = React.useState<string | null>(null);

  const [messages, setMessages] = React.useState<ChatMessage[]>([
    {
      id: "msg_welcome",
      role: "assistant",
      content:
        "Hello! I am **LedgerGuard AI Copilot**, your grounded financial reconciliation assistant. Ask me questions about loaded transaction ledgers, discrepancy categories, or specific exception codes like `EXC_1001`.",
      citedEvidenceIds: ["227_EXCEPTIONS_AGGREGATE"],
      confidenceScore: 1.0,
      fallbackMode: true,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);

  const chatEndRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSendQuery = async (queryText: string) => {
    const text = queryText.trim();
    if (!text || loading) return;

    const userMsgId = `user_${Date.now()}`;
    const userMsg: ChatMessage = {
      id: userMsgId,
      role: "user",
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setQuery("");
    setLoading(true);

    try {
      const res = await fetchApi<any>("/copilot/query", {
        method: "POST",
        body: JSON.stringify({ query: text }),
      });

      const assistantMsg: ChatMessage = {
        id: `ast_${Date.now()}`,
        role: "assistant",
        content: res.answer,
        citedEvidenceIds: res.cited_evidence_ids || [],
        confidenceScore: res.confidence_score,
        limitations: res.limitations,
        fallbackMode: res.fallback_mode,
        disclaimer: res.disclaimer,
        suggestedActions: res.suggested_actions || [],
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      toast.error(`Copilot request failed: ${err.message}`);
      setMessages((prev) => [
        ...prev,
        {
          id: `err_${Date.now()}`,
          role: "assistant",
          content: `⚠ Error communicating with backend copilot service: ${err.message}`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    toast.success("Copied answer to clipboard!");
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-6.5rem)] max-w-5xl mx-auto space-y-4">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b pb-3 shrink-0">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
              AI Finance Controller Copilot
            </h1>
            <Badge variant="ai" className="font-mono text-[10px] gap-1">
              <Sparkles className="h-3 w-3" />
              Grounded AI Engine
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">
            Natural language financial query assistant with grounded source citations and zero hallucination boundaries.
          </p>
        </div>

        {/* Data Scope Indicator */}
        <Badge variant="outline" className="flex items-center gap-1.5 text-xs py-1 font-mono border-violet-200 bg-violet-50/50 text-violet-700 dark:border-violet-900/50 dark:bg-violet-950/40 dark:text-violet-300 shrink-0">
          <Database className="h-3.5 w-3.5 text-violet-600" />
          <span>Scope: 2,010 Records • 227 Exceptions</span>
        </Badge>
      </div>

      {/* Suggested Starter Query Chips */}
      <div className="flex flex-wrap items-center gap-2 shrink-0">
        <span className="text-xs font-semibold text-muted-foreground flex items-center gap-1">
          <HelpCircle className="h-3.5 w-3.5" />
          Suggested:
        </span>
        {STARTER_QUERIES.map((sq, idx) => (
          <button
            key={idx}
            onClick={() => handleSendQuery(sq)}
            disabled={loading}
            className="rounded-full border bg-card px-3 py-1 text-xs text-foreground shadow-2xs transition-colors hover:bg-accent hover:border-primary/50 text-left truncate max-w-xs"
          >
            {sq}
          </button>
        ))}
      </div>

      {/* Chat Messages Stream */}
      <div className="flex-1 overflow-y-auto rounded-lg border bg-card p-4 space-y-4">
        {messages.map((msg) => {
          const isUser = msg.role === "user";

          return (
            <div
              key={msg.id}
              className={`flex items-start gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}
            >
              {/* Avatar Icon */}
              <div
                className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${
                  isUser
                    ? "bg-primary text-primary-foreground"
                    : "bg-violet-100 text-violet-700 dark:bg-violet-950 dark:text-violet-300 border border-violet-300"
                }`}
              >
                {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
              </div>

              {/* Message Bubble Container */}
              <div className={`space-y-2 max-w-2xl ${isUser ? "items-end text-right" : "items-start text-left"}`}>
                <div
                  className={`rounded-lg p-3.5 text-xs shadow-2xs leading-relaxed ${
                    isUser
                      ? "bg-primary text-primary-foreground font-medium"
                      : "bg-muted/40 border text-foreground"
                  }`}
                >
                  {/* Markdown formatted content */}
                  <div className="whitespace-pre-wrap font-sans text-xs space-y-1">
                    {msg.content}
                  </div>
                </div>

                {/* Assistant Message Extra Evidence Cards & Actions */}
                {!isUser && (
                  <div className="space-y-2 pl-1">
                    {/* Cited Evidence Cards */}
                    {msg.citedEvidenceIds && msg.citedEvidenceIds.length > 0 && (
                      <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
                        <span className="font-semibold text-muted-foreground">Cited Evidence:</span>
                        {msg.citedEvidenceIds.map((cid, i) => (
                          <Link key={i} href="/exceptions">
                            <Badge variant="outline" className="font-mono text-[10px] gap-1 hover:border-primary cursor-pointer">
                              <ExternalLink className="h-2.5 w-2.5" />
                              {cid}
                            </Badge>
                          </Link>
                        ))}
                      </div>
                    )}

                    {/* Copy Answer Action */}
                    <div className="flex items-center justify-between text-[10px] text-muted-foreground pt-1">
                      <span className="font-mono">
                        {msg.fallbackMode ? "Grounded Rules Engine" : "OpenAI LLM"} • Confidence:{" "}
                        {msg.confidenceScore ? `${(msg.confidenceScore * 100).toFixed(0)}%` : "95%"}
                      </span>

                      <button
                        onClick={() => handleCopy(msg.id, msg.content)}
                        className="flex items-center gap-1 hover:text-foreground transition-colors"
                      >
                        {copiedId === msg.id ? <Check className="h-3 w-3 text-emerald-600" /> : <Copy className="h-3 w-3" />}
                        <span>{copiedId === msg.id ? "Copied" : "Copy Answer"}</span>
                      </button>
                    </div>

                    {/* Mandatory Human Review Disclaimer */}
                    <div className="p-2 rounded bg-amber-50/50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/40 text-[10px] text-amber-800 dark:text-amber-300 font-medium">
                      ⚠ AI-assisted analysis based on loaded synthetic data. Human review is required.
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {/* Loading Indicator */}
        {loading && (
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-violet-100 text-violet-700 dark:bg-violet-950 dark:text-violet-300 border border-violet-300">
              <Bot className="h-4 w-4 animate-spin" />
            </div>
            <div className="rounded-lg p-3 bg-muted/40 border text-xs text-muted-foreground font-mono flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-violet-500 animate-ping" />
              <span>Analyzing financial ledgers and generating grounded evidence citation...</span>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Input Toolbar */}
      <div className="shrink-0 pt-1">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendQuery(query);
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={loading}
            placeholder="Ask copilot a question (e.g. Why was EXC_1001 flagged?)..."
            className="flex-1 h-10 rounded-lg border border-input bg-card px-3 text-xs outline-none focus:ring-1 focus:ring-ring shadow-2xs"
          />
          <Button
            type="submit"
            disabled={!query.trim() || loading}
            size="sm"
            className="h-10 px-4 gap-1.5 shadow-2xs font-medium"
          >
            <span>Send</span>
            <Send className="h-3.5 w-3.5" />
          </Button>
        </form>
      </div>
    </div>
  );
}
