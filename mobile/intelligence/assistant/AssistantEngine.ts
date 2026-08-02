/** AI Assistant — types, config, knowledge, prompts, RAG, chat, streaming, memory */
export type AssistantMode = 'search' | 'qa' | 'compare' | 'explain' | 'summarize' | 'analyze';
export type MessageRole = 'user' | 'assistant' | 'system' | 'citation';
export type StreamStatus = 'idle' | 'streaming' | 'complete' | 'error' | 'cancelled';
export type KnowledgeSource = 'backend' | 'prediction_engine' | 'ranking_engine' | 'statistics' | 'recommendations' | 'knowledge_graph';

export interface ChatMessage { id: string; role: MessageRole; content: string; citations?: Citation[]; timestamp: number; }
export interface Citation { source: KnowledgeSource; documentId: string; title: string; excerpt: string; relevanceScore: number; }
export interface Conversation { id: string; title: string; messages: ChatMessage[]; createdAt: number; updatedAt: number; pinned: boolean; }
export interface AssistantConfig { modelName: string; maxTokens: number; temperature: number; topP: number; maxContextMessages: number; enableStreaming: boolean; enableCitations: boolean; enableMemory: boolean; maxConversations: number; }
export interface RetrievalResult { documentId: string; source: KnowledgeSource; content: string; relevanceScore: number; metadata: Record<string, any>; }
export interface PromptTemplate { name: string; system: string; temperature: number; maxTokens: number; }

export const defaultAssistantConfig: AssistantConfig = { modelName: 'gpt-4o', maxTokens: 2048, temperature: 0.7, topP: 0.9, maxContextMessages: 20, enableStreaming: true, enableCitations: true, enableMemory: true, maxConversations: 50 };
let _ac: Partial<AssistantConfig> = {};
export const assistantConfig = { get: (): AssistantConfig => ({ ...defaultAssistantConfig, ..._ac }), update: (p: Partial<AssistantConfig>) => { Object.assign(_ac, p); } };

export const PROMPT_TEMPLATES: Record<string, PromptTemplate> = {
  mma_expert: { name: 'MMA Expert', system: 'You are an MMA expert analyst. Answer questions using factual fighter data, statistics, and fight analysis. Be concise and data-driven.', temperature: 0.5, maxTokens: 1024 },
  compare: { name: 'Fighter Comparison', system: 'Compare two fighters objectively using their records, styles, statistics, and recent performances. Present a balanced analysis of advantages for each.', temperature: 0.3, maxTokens: 1500 },
  explain_prediction: { name: 'Prediction Explainer', system: 'Explain MMA fight predictions clearly. Break down contributing factors: recent form, style matchup, physical attributes, and historical data.', temperature: 0.4, maxTokens: 1024 },
};

export class AssistantLogger { private p = '[Assistant]'; info(m: string) { console.log(`${this.p} ${m}`); } error(m: string) { console.error(`${this.p} ${m}`); } }
export const aiLogger = new AssistantLogger();
export const aiUtils = { generateId: (): string => `msg-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`, generateConvId: (): string => `conv-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`, truncateContext: (messages: ChatMessage[], max: number): ChatMessage[] => messages.slice(-max), };

/** RAG Knowledge Retrieval */
export class KnowledgeRetriever {
  async retrieve(query: string, sources: KnowledgeSource[] = ['backend', 'prediction_engine', 'ranking_engine', 'statistics']): Promise<RetrievalResult[]> {
    const results: RetrievalResult[] = [];
    for (const source of sources) {
      const docs = await this.querySource(source, query);
      results.push(...docs);
    }
    return results.sort((a, b) => b.relevanceScore - a.relevanceScore).slice(0, 10);
  }

  private async querySource(source: KnowledgeSource, query: string): Promise<RetrievalResult[]> {
    // In production: call backend search/vector DB
    return [{ documentId: `${source}-1`, source, content: `Results for: ${query} from ${source}`, relevanceScore: 0.85, metadata: {} }];
  }
}
export const knowledgeRetriever = new KnowledgeRetriever();

/** Memory Manager */
export class MemoryManager {
  private conversations = new Map<string, Conversation>();
  private currentId: string | null = null;

  createConversation(title = 'New Conversation'): Conversation {
    const conv: Conversation = { id: aiUtils.generateConvId(), title, messages: [], createdAt: Date.now(), updatedAt: Date.now(), pinned: false };
    if (this.conversations.size >= assistantConfig.get().maxConversations) { const oldest = [...this.conversations.entries()].sort((a, b) => a[1].updatedAt - b[1].updatedAt)[0]; if (oldest?.[0]) this.conversations.delete(oldest[0]); }
    this.conversations.set(conv.id, conv); this.currentId = conv.id; return conv;
  }

  getCurrent(): Conversation | null { return this.currentId ? this.conversations.get(this.currentId) || null : null; }
  getAll(): Conversation[] { return [...this.conversations.values()].sort((a, b) => b.updatedAt - a.updatedAt); }
  getHistory(): ChatMessage[] { return this.getCurrent()?.messages || []; }

  addMessage(message: ChatMessage): void {
    const conv = this.getCurrent(); if (!conv) return;
    conv.messages.push(message); conv.updatedAt = Date.now();
    if (conv.messages.length === 2) conv.title = conv.messages[0].content.slice(0, 50);
  }

  pin(id: string): void { const c = this.conversations.get(id); if (c) c.pinned = true; }
  delete(id: string): void { this.conversations.delete(id); if (this.currentId === id) this.currentId = null; }
  clear(): void { this.conversations.clear(); this.currentId = null; }
}
export const memoryManager = new MemoryManager();

/** Chat Engine */
export class ChatEngine {
  private streaming = false;
  private cancelFlag = false;

  async sendMessage(content: string): Promise<ChatMessage> {
    const userMsg: ChatMessage = { id: aiUtils.generateId(), role: 'user', content, timestamp: Date.now() };
    memoryManager.addMessage(userMsg);

    const history = memoryManager.getHistory();
    const context = aiUtils.truncateContext(history, assistantConfig.get().maxContextMessages);

    const retrieved = await knowledgeRetriever.retrieve(content);
    const contextStr = retrieved.map((r) => r.content).join('\n---\n');

    const systemPrompt = PROMPT_TEMPLATES.mma_expert.system + `\n\nRelevant data:\n${contextStr}`;

    const response = await this.generate(systemPrompt, context, content);
    const citations: Citation[] = retrieved.slice(0, 5).map((r) => ({ source: r.source, documentId: r.documentId, title: r.metadata?.title || r.source, excerpt: r.content.slice(0, 100), relevanceScore: r.relevanceScore }));

    const aiMsg: ChatMessage = { id: aiUtils.generateId(), role: 'assistant', content: response, citations, timestamp: Date.now() };
    memoryManager.addMessage(aiMsg);
    return aiMsg;
  }

  async streamMessage(content: string, onChunk: (text: string) => void): Promise<ChatMessage> {
    this.streaming = true; this.cancelFlag = false;
    const userMsg: ChatMessage = { id: aiUtils.generateId(), role: 'user', content, timestamp: Date.now() };
    memoryManager.addMessage(userMsg);

    let full = '';
    const words = `Response: ${content}`.split(' ');
    for (const word of words) {
      if (this.cancelFlag) break;
      full += word + ' ';
      onChunk(word + ' ');
      await new Promise((r) => setTimeout(r, 30));
    }
    this.streaming = false;

    const aiMsg: ChatMessage = { id: aiUtils.generateId(), role: 'assistant', content: full.trim(), timestamp: Date.now() };
    memoryManager.addMessage(aiMsg);
    return aiMsg;
  }

  cancel(): void { if (this.streaming) this.cancelFlag = true; }
  isStreaming(): boolean { return this.streaming; }

  private async generate(systemPrompt: string, context: ChatMessage[], query: string): Promise<string> {
    // In production: call LLM API with system prompt + context + query
    return `Based on the data, here's what I found about "${query}": Analysis results would appear here with detailed fighter statistics, comparisons, and predictions.`;
  }
}
export const chatEngine = new ChatEngine();

/** Analytics */
export class AssistantAnalytics {
  trackConversation(count: number): void {}
  trackQuestion(type: AssistantMode): void {}
  trackLatency(ms: number): void {}
  trackTokenUsage(tokens: number): void {}
  trackSatisfaction(score: number): void {}
}
export const assistantAnalytics = new AssistantAnalytics();
