import type { AppState } from '../stores/appStore';

// Types for API requests and responses
interface SystemSettings {
  cutoffVoltage: number;
  motorCurrentThreshold: number;
  switchCurrentThreshold: number;
  cycleLimit: number;
  motorFailureThreshold: number;
  switchFailureThreshold: number;
  cyclesPerMinute: number;
}

interface Station {
  id: number;
  enabled: boolean;
  motorFailures: number;
  switchFailures: number;
  currentCycles: number;
  motorCurrent: number;
  switchCurrent: number;
}

interface SystemState {
  masterEnabled: boolean;
  supplyVoltage: number;
  timerActive: boolean;
  timerHours: number;
  timerMinutes: number;
  timerSeconds: number;
  stations: Station[];
}

// WebSocket connection
let ws: WebSocket | null = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY = 2000;

// Event handlers type
type MessageHandler = (data: any) => void;

// Message handlers for different event types
const messageHandlers: { [key: string]: MessageHandler[] } = {};

// Initialize WebSocket connection
export function initializeWebSocket() {
  if (ws) return;

  ws = new WebSocket('ws://192.168.75.77:8000/ws');

  ws.onopen = () => {
    console.log('WebSocket connected');
    reconnectAttempts = 0;
  };

  ws.onmessage = (event) => {
    try {
      const message = JSON.parse(event.data);
      const handlers = messageHandlers[message.type];
      if (handlers) {
        handlers.forEach(handler => handler(message.data));
      }
    } catch (e) {
      console.error('Error processing WebSocket message:', e);
    }
  };

  ws.onclose = () => {
    console.log('WebSocket disconnected');
    ws = null;

    // Try to reconnect if we haven't exceeded max attempts
    if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
      reconnectAttempts++;
      console.log(`Reconnecting... Attempt ${reconnectAttempts}`);
      setTimeout(initializeWebSocket, RECONNECT_DELAY);
    } else {
      console.error('Max reconnection attempts reached');
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };
}

// Register message handler
export function onMessage(type: string, handler: MessageHandler) {
  if (!messageHandlers[type]) {
    messageHandlers[type] = [];
  }
  messageHandlers[type].push(handler);
  return () => {
    messageHandlers[type] = messageHandlers[type].filter(h => h !== handler);
  };
}

// Send message to server
export function sendMessage(type: string, data: any) {
  if (!ws || typeof window === 'undefined') return;
  
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type, data }));
  } else {
    console.error('WebSocket is not connected');
  }
}

// API endpoints
const API_BASE_URL = 'http://192.168.75.77:8000/api';

// HTTP request helper
async function fetchWithError(url: string, options: RequestInit = {}) {
  try {
    const response = await fetch(url, {
      ...options,
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      throw new Error(errorData?.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}

// API functions
export const api = {
  // Authentication
  async authenticate(pin: string): Promise<boolean> {
    const response = await fetch(`${API_BASE_URL}/auth?pin=${pin}`, {
      credentials: 'include'
    });
    const data = await response.json();
    return data.success;
  },

  // Settings
  async getSettings(): Promise<Partial<AppState>> {
    const response = await fetch(`${API_BASE_URL}/settings`, {
      credentials: 'include'
    });
    return response.json();
  },

  async updateSettings(settings: Partial<AppState>): Promise<boolean> {
    const response = await fetch(`${API_BASE_URL}/settings`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(settings),
    });
    const data = await response.json();
    return data.success;
  },

  // System status
  async getStatus(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/status`, {
      credentials: 'include'
    });
    return response.json();
  },

  // Test control
  async startTest(): Promise<boolean> {
    const response = await fetch(`${API_BASE_URL}/test/start`, {
      method: 'POST',
      credentials: 'include'
    });
    const data = await response.json();
    return data.success;
  },

  async stopTest(): Promise<boolean> {
    const response = await fetch(`${API_BASE_URL}/test/stop`, {
      method: 'POST',
      credentials: 'include'
    });
    const data = await response.json();
    return data.success;
  },

  // Station control
  async setStationState(stationId: number, enabled: boolean): Promise<void> {
    await fetchWithError(`${API_BASE_URL}/station/${stationId}/state`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ enabled })
    });
  },

  // Timer
  async setTimer(hours: number, minutes: number): Promise<boolean> {
    const response = await fetch(`${API_BASE_URL}/timer`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ hours, minutes }),
    });
    const data = await response.json();
    return data.success;
  },
}; 
