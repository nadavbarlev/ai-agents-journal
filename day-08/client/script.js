class ChatAgent {
    constructor() {
        this.chatMessages = document.getElementById('chat-messages');
        this.messageInput = document.getElementById('message-input');
        this.sendButton = document.getElementById('send-button');
        this.status = document.getElementById('status');
        this.agentName = document.getElementById('agent-name');
        this.agentInstructions = document.getElementById('agent-instructions');

        this.isStreaming = false;
        this.currentStreamingMessage = null;

        this.initializeEventListeners();
        this.enableInterface();
    }

    initializeEventListeners() {
        // Send button click
        this.sendButton.addEventListener('click', () => this.sendMessage());

        // Enter key in message input (Shift+Enter for new line)
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Enable send button when there's content
        this.messageInput.addEventListener('input', () => {
            const hasContent = this.messageInput.value.trim().length > 0;
            this.sendButton.disabled = !hasContent || this.isStreaming;
        });

        // Auto-resize message input
        this.messageInput.addEventListener('input', () => {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = this.messageInput.scrollHeight + 'px';
        });
    }

    enableInterface() {
        this.messageInput.disabled = false;
        this.sendButton.disabled = true;
        this.status.textContent = 'Ready to chat';
        this.status.className = 'status';
    }

    disableInterface() {
        this.messageInput.disabled = true;
        this.sendButton.disabled = true;
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isStreaming) return;

        const agentName = this.agentName.value.trim() || 'Assistant';
        const agentInstructions = this.agentInstructions.value.trim() || 'You are a helpful assistant.';

        // Add user message to chat
        this.addMessage(message, 'user');

        // Clear input and disable interface
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';
        this.disableInterface();

        // Set streaming status
        this.isStreaming = true;
        this.status.textContent = 'Connecting...';
        this.status.className = 'status connecting';

        try {
            // Make the streaming request
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    agent_name: agentName,
                    agent_instructions: agentInstructions
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // Process the streaming response
            await this.processStreamingResponse(response);

        } catch (error) {
            console.error('Error:', error);
            this.addMessage('Sorry, there was an error processing your request.', 'system');
            this.status.textContent = 'Error occurred';
            this.status.className = 'status error';
        } finally {
            this.isStreaming = false;
            this.enableInterface();
        }
    }

    async processStreamingResponse(response) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        this.status.textContent = 'Streaming response...';
        this.status.className = 'status streaming';

        // Initialize streaming message container
        this.currentStreamingMessage = this.createStreamingMessage();

        try {
            while (true) {
                const { done, value } = await reader.read();

                if (done) break;

                // Decode the chunk
                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            this.handleStreamEvent(data);
                        } catch (e) {
                            console.warn('Failed to parse JSON:', line, e);
                        }
                    }
                }
            }
        } finally {
            reader.releaseLock();
            this.finalizeStreamingMessage();
        }
    }

    handleStreamEvent(data) {
        switch (data.type) {
            case 'start':
                console.log('Stream started:', data.message);
                break;

            case 'token':
                if (data.content) {
                    this.appendToStreamingMessage(data.content);
                }
                break;

            case 'message':
                if (data.content) {
                    this.appendToStreamingMessage(data.content);
                }
                break;

            case 'message_replace':
                if (data.content) {
                    this.replaceStreamingMessage(data.content);
                }
                break;

            case 'agent_update':
                console.log('Agent updated:', data.agent_name);
                break;

            case 'tool_call':
                this.appendToStreamingMessage('\n[Tool called]');
                break;

            case 'tool_output':
                this.appendToStreamingMessage(`\n[Tool output: ${data.content}]`);
                break;

            case 'complete':
                console.log('Stream completed');
                this.status.textContent = 'Response complete';
                break;

            default:
                console.log('Unknown event type:', data);
        }
    }

    createStreamingMessage() {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message streaming-message';
        messageDiv.innerHTML = '<span class="typing-indicator"></span>';
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
        return messageDiv;
    }

    appendToStreamingMessage(content) {
        if (!this.currentStreamingMessage) return;

        // Remove typing indicator if it exists
        const typingIndicator = this.currentStreamingMessage.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }

        // Append the content
        this.currentStreamingMessage.textContent += content;
        this.scrollToBottom();
    }

    replaceStreamingMessage(content) {
        if (!this.currentStreamingMessage) return;

        // Remove typing indicator if it exists
        const typingIndicator = this.currentStreamingMessage.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }

        // Replace the content entirely
        this.currentStreamingMessage.textContent = content;
        this.scrollToBottom();
    }

    finalizeStreamingMessage() {
        if (!this.currentStreamingMessage) return;

        // Remove typing indicator
        const typingIndicator = this.currentStreamingMessage.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }

        // Change class to final assistant message
        this.currentStreamingMessage.className = 'message assistant-message';

        // If the message is empty, add a default message
        if (!this.currentStreamingMessage.textContent.trim()) {
            this.currentStreamingMessage.textContent = 'No response received.';
        }

        this.currentStreamingMessage = null;
        this.scrollToBottom();
    }

    addMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        messageDiv.textContent = content;
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
}

// Initialize the chat when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new ChatAgent();
});