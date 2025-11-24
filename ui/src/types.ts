

// ComfyUI Workflow Data Structures

export interface ComfyNodeInput {
    name: string;
    type: string;
    link?: number | null;
}

export interface ComfyNodeOutput {
    name: string;
    type: string;
    links?: number[];
    slot_index?: number;
}

export interface ComfyNode {
    id: number;
    type: string;
    pos: [number, number];
    size: { 0: number; 1: number } | number[];
    flags: Record<string, any>;
    order: number;
    mode: number;
    inputs?: ComfyNodeInput[];
    outputs?: ComfyNodeOutput[];
    properties?: Record<string, any>;
    widgets_values?: any[];
    color?: string;
    bgcolor?: string;
}

// Changed from interface to tuple type for array destructuring support
export type ComfyLink = [number, number, number, number, number, string];

export interface ComfyWorkflow {
    last_node_id: number;
    last_link_id: number;
    nodes: ComfyNode[];
    links: ComfyLink[];
    groups: any[];
    config: any;
    extra: any;
    version: number;
}

export interface WorkflowCheckpoint {
    id: string;
    timestamp: number;
    name: string;
    data: ComfyWorkflow;
}

// App Logic Types

export enum Sender {
    USER = 'user',
    AI = 'ai',
    SYSTEM = 'system'
}

export interface ChatMessage {
    id: string;
    sender: Sender;
    text: string;
    timestamp: Date;
    metadata?: {
        thinking?: boolean;
        workflowUpdate?: boolean;
        suggestedActions?: string[];
        missingNodes?: string[];
        groundingSources?: Array<{ uri: string; title: string }>;
        provider?: string; // To show which model generated this
    };
}

export interface GeminiResponseSchema {
    chatResponse: string;
    updatedWorkflow?: ComfyWorkflow | null;
    missingNodes?: string[];
    suggestedActions?: string[];
    groundingSources?: Array<{ uri: string; title: string }>;
    issues?: WorkflowIssue[];
}

// Settings & Diagnostics

export type AIProvider = 'google' | 'custom';
export type Language = 'en' | 'zh' | 'ja' | 'ko';

export interface AppSettings {
    provider: AIProvider;
    apiKey: string; // For Google or Custom (if needed)
    modelName: string; // e.g., "gemini-2.5-flash" or "llama3"
    baseUrl?: string; // For custom/local (e.g., "http://localhost:11434/v1")
    language: Language;
}

export type IssueSeverity = 'error' | 'warning' | 'info';

export interface WorkflowIssue {
    id: string;
    nodeId: number | null;
    severity: IssueSeverity;
    message: string;
    fixSuggestion?: string;
}
