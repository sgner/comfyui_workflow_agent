
import { GoogleGenAI } from "@google/genai";
import { ComfyWorkflow, GeminiResponseSchema, AppSettings, WorkflowIssue } from '../types';

const BASE_SYSTEM_INSTRUCTION = `
You are "Comfy Workflow Agent", an expert AI assistant and Workflow Architect specialized in ComfyUI.
Your goal is to help users build, fix, debug, and understand ComfyUI workflows.

## CAPABILITIES
1. **Analyze Workflows**: Understand the structure, data flow, and logic of the provided JSON.
2. **Modify Workflows**: Generate a VALID, COMPLETE JSON representation of the workflow when requested.
3. **Diagnose Issues**: When asked to diagnose, identify logical errors, incompatible types, or broken flows.

## RESPONSE FORMAT
1. **For General Advice**: Natural language.
2. **For Workflow Updates**:
   - Output the **FULL JSON** in a Markdown code block labeled \`json\`.
   - Example: \`\`\`json { ... } \`\`\`
   - **CRITICAL**: Ensure valid JSON. NO trailing commas. NO comments inside the JSON block.
3. **For Diagnostics / Issues**:
   - If you find specific problems, output them in a JSON array block labeled \`ISSUES_JSON\`.
   - Format: \`ISSUES_JSON: [{"nodeId": 10, "severity": "error", "message": "...", "fixSuggestion": "..."}]\`
4. **For Missing Nodes**:
   - Use a section: "SUGGESTED_ACTIONS: [Action1, Action2]".

## RULES
- **Always** validate connections.
- **Never** break JSON structure.
`;

// --- Helper for Custom OpenAI-Compatible Calls ---
async function callCustomLLM(settings: AppSettings, prompt: string, systemInstruction: string): Promise<string> {
    if (!settings.baseUrl) throw new Error("Base URL required for custom provider");

    const response = await fetch(`${settings.baseUrl.replace(/\/$/, '')}/chat/completions`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${settings.apiKey || 'not-needed'}`
        },
        body: JSON.stringify({
            model: settings.modelName,
            messages: [
                { role: "system", content: systemInstruction },
                { role: "user", content: prompt }
            ],
            temperature: 0.5
        })
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Custom LLM Error: ${settings.baseUrl} returned ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    return data.choices?.[0]?.message?.content || "";
}

// --- Helper for Google Gemini Calls ---
async function callGoogleGemini(settings: AppSettings, prompt: string, systemInstruction: string): Promise<{text: string, sources: Array<{uri:string, title:string}>}> {
    // STRICT: Use process.env.API_KEY directly.
    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

    const response = await ai.models.generateContent({
        model: settings.modelName || 'gemini-2.5-flash',
        contents: prompt,
        config: {
            systemInstruction: systemInstruction,
            tools: [{ googleSearch: {} }],
            temperature: 0.5,
        }
    });

    const text = response.text || "";
    const groundingChunks = response.candidates?.[0]?.groundingMetadata?.groundingChunks;
    const sources: Array<{ uri: string; title: string }> = [];

    if (groundingChunks) {
        groundingChunks.forEach(chunk => {
            if (chunk.web?.uri && chunk.web?.title) {
                sources.push({ uri: chunk.web.uri, title: chunk.web.title });
            }
        });
    }

    return { text, sources };
}

// --- Parsing Helpers ---

function cleanJsonString(jsonStr: string): string {
    // 1. Remove single line comments // ...
    let clean = jsonStr.replace(/\/\/.*$/gm, "");
    // 2. Remove multi-line comments /* ... */
    clean = clean.replace(/\/\*[\s\S]*?\*\//g, "");
    // 3. Attempt to remove trailing commas (simplistic approach: , before })
    clean = clean.replace(/,\s*}/g, '}').replace(/,\s*]/g, ']');
    return clean;
}

// --- Main Service Function ---

export const sendMessageToComfyAgent = async (
    currentWorkflow: ComfyWorkflow,
    userPrompt: string,
    settings: AppSettings,
    _history: string[] = []
): Promise<GeminiResponseSchema> => {

    try {
        const prompt = `
        [CURRENT WORKFLOW STATE]
        Node Count: ${currentWorkflow?.nodes?.length || 0}
        Nodes Summary: ${JSON.stringify(currentWorkflow?.nodes?.map(n => ({id: n.id, type: n.type, title: n.properties?.['Node name for S&R']})) || [])}

        [FULL WORKFLOW JSON]
        ${JSON.stringify(currentWorkflow)}

        [USER REQUEST]
        "${userPrompt}"

        [INSTRUCTIONS]
        - If the user wants to change the workflow, output the NEW JSON in a \`\`\`json block.
        - If the user asks to DIAGNOSE, ANALYZE, or CHECK the workflow, output the issues in \`ISSUES_JSON: [...] \`.
        - Suggest 2-3 short follow-up actions if applicable in the format "SUGGESTED_ACTIONS: [Action 1, Action 2]".
        `;

        // Inject Language Instruction
        const languageInstruction = `\nIMPORTANT: You MUST respond in the following language code: "${settings.language}". Translate your advice and interface text accordingly.`;
        const fullSystemInstruction = BASE_SYSTEM_INSTRUCTION + languageInstruction;

        let textResponse = "";
        let sources: Array<{ uri: string; title: string }> = [];

        if (settings.provider === 'google') {
            const res = await callGoogleGemini(settings, prompt, fullSystemInstruction);
            textResponse = res.text;
            sources = res.sources;
        } else {
            // Custom / Local
            textResponse = await callCustomLLM(settings, prompt, fullSystemInstruction);
        }

        // --- Parsing Logic (Shared) ---

        // 1. Extract Workflow JSON
        let updatedWorkflow: ComfyWorkflow | null = null;
        const jsonMatch = textResponse.match(/```json\s*([\s\S]*?)\s*```/);

        if (jsonMatch && jsonMatch[1]) {
            try {
                const rawJson = jsonMatch[1];
                const cleanedJson = cleanJsonString(rawJson);
                updatedWorkflow = JSON.parse(cleanedJson);
            } catch (e) {
                console.error("Failed to parse generated workflow JSON:", e);
                textResponse += `\n\n(Note: I generated a workflow update, but there was a technical error reading it. Error: ${(e as Error).message})`;
            }
        }

        // 2. Extract Issues
        let issues: WorkflowIssue[] = [];
        const issuesMatch = textResponse.match(/ISSUES_JSON:\s*(\[[\s\S]*?\])/);
        if (issuesMatch && issuesMatch[1]) {
            try {
                const rawIssues = issuesMatch[1];
                const parsedIssues = JSON.parse(cleanJsonString(rawIssues));
                if (Array.isArray(parsedIssues)) {
                    issues = parsedIssues.map((issue: any, idx: number) => ({
                        id: `ai-issue-${Date.now()}-${idx}`,
                        nodeId: issue.nodeId || null,
                        severity: issue.severity || 'warning',
                        message: issue.message || 'Unknown issue',
                        fixSuggestion: issue.fixSuggestion
                    }));
                }
            } catch (e) {
                console.error('Failed to parse issues JSON:', e);
            }
        }

        // 3. Extract Suggested Actions
        let suggestedActions: string[] = [];
        const actionsMatch = textResponse.match(/SUGGESTED_ACTIONS:\s*\[(.*?)\]/);
        if (actionsMatch && actionsMatch[1]) {
            suggestedActions = actionsMatch[1].split(',').map(s => s.trim().replace(/['"]/g, ''));
        }

        // 4. Clean up the chat response for display
        const cleanText = textResponse
            .replace(/```json\s*[\s\S]*?\s*```/, '(Workflow updated below...)')
            .replace(/ISSUES_JSON:\s*\[[\s\S]*?\]/, '')
            .replace(/SUGGESTED_ACTIONS:\s*\[.*?\]/, '')
            .trim();

        return {
            chatResponse: cleanText,
            updatedWorkflow: updatedWorkflow,
            missingNodes: [],
            issues: issues,
            suggestedActions: suggestedActions.length > 0 ? suggestedActions : ["Undo", "Explain changes"],
            groundingSources: sources
        };

    } catch (error: any) {
        console.error("AI Agent Error:", error);
        return {
            chatResponse: `Error communicating with ${settings.provider === 'google' ? 'Gemini' : 'Local Model'}: ${error.message || 'Unknown error'}`,
            updatedWorkflow: null,
            suggestedActions: ["Check Settings", "Retry"],
            groundingSources: []
        };
    }
};
