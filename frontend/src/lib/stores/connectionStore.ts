import { writable } from 'svelte/store';
import { initializeWebSocket } from '../services/api';

export type ConnectionState = {
    isInitializing: boolean;      // True during initial connection attempt
    isConnected: boolean;         // True when WebSocket is connected
    isDataLoaded: boolean;        // True when initial API data is loaded
    reconnectAttempt: number;     // Current reconnection attempt number
    hasReachedMaxAttempts: boolean; // Whether max reconnection attempts have been reached
};

const initialState: ConnectionState = {
    isInitializing: true,
    isConnected: false,
    isDataLoaded: false,
    reconnectAttempt: 0,
    hasReachedMaxAttempts: false
};

function createConnectionStore() {
    const { subscribe, set, update } = writable<ConnectionState>(initialState);

    return {
        subscribe,
        
        // Called when WebSocket connects
        setConnected: () => update(state => ({
            ...state,
            isConnected: true,
            reconnectAttempt: 0,
            hasReachedMaxAttempts: false
        })),

        // Called when WebSocket disconnects
        setDisconnected: () => update(state => ({
            ...state,
            isConnected: false
        })),

        // Called when reconnection attempt starts
        setReconnecting: (attempt: number) => update(state => ({
            ...state,
            reconnectAttempt: attempt,
            isConnected: false
        })),

        // Called when max attempts are reached
        setMaxAttemptsReached: () => update(state => ({
            ...state,
            hasReachedMaxAttempts: true,
            isConnected: false
        })),

        // Called when retry button is pressed
        retry: () => {
            update(state => ({
                ...state,
                reconnectAttempt: 0,
                hasReachedMaxAttempts: false,
                isInitializing: true
            }));
            initializeWebSocket(true);
        },

        // Called when initial data is loaded
        setDataLoaded: () => {
            // First update to show we have data
            update(state => ({
                ...state,
                isDataLoaded: true
            }));
            
            // Add a delay before completing initialization
            setTimeout(() => {
                update(state => ({
                    ...state,
                    isInitializing: false
                }));
            }, 500); // 500ms delay
        },

        // Reset to initial state
        reset: () => set(initialState)
    };
}

export const connectionStore = createConnectionStore(); 