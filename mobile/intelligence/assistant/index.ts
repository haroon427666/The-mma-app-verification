/** AI Assistant — hooks + index */
import { useState, useCallback, useEffect } from 'react';
import { chatEngine, memoryManager, knowledgeRetriever, assistantConfig, PROMPT_TEMPLATES, assistantAnalytics, aiLogger } from './AssistantEngine';
import type { ChatMessage, Conversation } from './AssistantEngine';

export function useAssistant() {
  const [messages, setMessages] = useState<ChatMessage[]>(() => memoryManager.getHistory());
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);

  const send = useCallback(async (content: string) => {
    setLoading(true);
    try {
      const msg = await chatEngine.sendMessage(content);
      setMessages(memoryManager.getHistory());
      return msg;
    } finally { setLoading(false); }
  }, []);

  const sendStream = useCallback(async (content: string, onChunk?: (text: string) => void) => {
    setStreaming(true);
    try {
      const msg = await chatEngine.streamMessage(content, (chunk) => { setMessages(memoryManager.getHistory()); onChunk?.(chunk); });
      setMessages(memoryManager.getHistory());
      return msg;
    } finally { setStreaming(false); }
  }, []);

  const cancel = useCallback(() => chatEngine.cancel(), []);
  const newConversation = useCallback(() => { memoryManager.createConversation(); setMessages([]); }, []);
  const clearHistory = useCallback(() => { memoryManager.clear(); setMessages([]); }, []);

  return { messages, send, sendStream, cancel, loading, streaming, newConversation, clearHistory, conversations: memoryManager.getAll() };
}

export function useConversations() {
  const [convs, setConvs] = useState<Conversation[]>(() => memoryManager.getAll());
  const refresh = useCallback(() => setConvs(memoryManager.getAll()), []);
  return { conversations: convs, refresh, pin: memoryManager.pin.bind(memoryManager), delete: memoryManager.delete.bind(memoryManager) };
}

export function useKnowledge(query?: string) {
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const search = useCallback(async (q: string) => { setLoading(true); try { const r = await knowledgeRetriever.retrieve(q); setResults(r); return r; } finally { setLoading(false); } }, []);
  useEffect(() => { if (query) search(query); }, [query, search]);
  return { results, search, loading };
}

/*
## MMA AI Assistant

### Architecture
```
User Question
  → KnowledgeRetriever.retrieve(query, sources) → vector DB/backend APIs
  → MemoryManager.getHistory() → conversation context
  → ChatEngine.generate(system + context + query) → LLM
  → Response with citations from relevant data sources

### Knowledge Sources
- Backend APIs (fighters, events, rankings)
- Prediction Engine (fight predictions)
- Ranking Engine (P4P, division rankings)
- Statistics Engine (fighter stats)
- Recommendation Engine (personalized)
- Knowledge Graph (relationships)

### Hooks
- useAssistant() → send, sendStream, messages, conversations
- useConversations() → list, pin, delete
- useKnowledge() → semantic search across knowledge base
*/

export { chatEngine, memoryManager, knowledgeRetriever, assistantConfig, PROMPT_TEMPLATES, assistantAnalytics, aiLogger, aiUtils } from './AssistantEngine';
export type { ChatMessage, Citation, Conversation, AssistantConfig, RetrievalResult, PromptTemplate, MessageRole, AssistantMode, KnowledgeSource, StreamStatus } from './AssistantEngine';
