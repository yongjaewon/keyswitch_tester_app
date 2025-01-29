import { writable, get } from 'svelte/store';
import { api, initializeWebSocket, onMessage } from '../services/api';

// Types
export interface Station {
  id: number;
  enabled: boolean;
  motorFailures: number;
  switchFailures: number;
  currentCycles: number;
  motorCurrent: string;
  switchCurrent: string;
}

export interface AppState {
  currentPage: 'test' | 'data';
  showTimerModal: boolean;
  showSettingsModal: boolean;
  showStationSettingsModal: boolean;
  masterEnabled: boolean;
  cutoffVoltage: number;
  motorFailureThreshold: number;
  switchFailureThreshold: number;
  cycleLimit: number;
  motorCurrentThreshold: number;
  switchCurrentThreshold: number;
  cyclesPerMinute: number;
  timerHours: number;
  timerMinutes: number;
  timerSeconds: number;
  timerActive: boolean;
  stations: Station[];
  selectedStation: Station | null;
  supplyVoltage: number;
}

// Initial state
const initialState: AppState = {
  currentPage: 'test',
  showTimerModal: false,
  showSettingsModal: false,
  showStationSettingsModal: false,
  masterEnabled: false,
  cutoffVoltage: 11.1,
  motorFailureThreshold: 10,
  switchFailureThreshold: 10,
  cycleLimit: 100000,
  motorCurrentThreshold: 100,
  switchCurrentThreshold: 5,
  cyclesPerMinute: 6,
  timerHours: 0,
  timerMinutes: 0,
  timerSeconds: 0,
  timerActive: false,
  selectedStation: null,
  supplyVoltage: 13.2,
  stations: [1, 2, 3, 4].map(num => ({
    id: num,
    enabled: num === 1 || num === 2,
    motorFailures: num === 1 ? 0 : num === 2 ? 3 : num === 3 ? 8 : 12,
    switchFailures: num === 1 ? 0 : num === 2 ? 4 : num === 3 ? 9 : 10,
    currentCycles: num === 1 ? 102235 : num === 2 ? 206 : num === 3 ? 4 : 25918,
    motorCurrent: num === 1 ? "120.0 A" : num === 2 ? "85.5 A" : num === 3 ? "105.2 A" : "45.8 A",
    switchCurrent: num === 1 ? "6.2 A" : num === 2 ? "3.8 A" : num === 3 ? "5.5 A" : "2.1 A"
  }))
};

// Create the store
export const appStore = writable<AppState>(initialState);

// Register WebSocket message handlers
onMessage('status_update', (data) => {
  appStore.update(state => {
    // Only update if we're not in a modal
    if (state.showTimerModal || state.showSettingsModal || state.showStationSettingsModal) {
      return state;
    }
    return {
      ...state,
      supplyVoltage: data.supplyVoltage,
      masterEnabled: data.masterEnabled,
      stations: data.stations
    };
  });
});

onMessage('timerUpdate', (data) => {
  appStore.update(state => {
    // Only update if we're not in timer modal
    if (state.showTimerModal) {
      return state;
    }
    return {
      ...state,
      timerHours: data.hours,
      timerMinutes: data.minutes,
      timerSeconds: data.seconds
    };
  });
});

// Store actions
export const actions = {
  toggleRunning: async () => {
    const state = get(appStore);
    const newMasterEnabled = !state.masterEnabled;

    try {
      // Call the API first
      if (newMasterEnabled) {
        await api.startTest();
      } else {
        await api.stopTest();
      }

      // Update state only after successful API call
      appStore.update(state => {
        const newState = { ...state, masterEnabled: newMasterEnabled };
        if (!newState.masterEnabled && newState.timerActive) {
          newState.timerActive = false;
          newState.timerHours = 0;
          newState.timerMinutes = 0;
          newState.timerSeconds = 0;
        }
        return newState;
      });
    } catch (error) {
      console.error('Error toggling test state:', error);
    }
  },

  toggleStation: async (stationId: number) => {
    let previousState: Station | undefined;
    
    appStore.update(state => {
      previousState = state.stations.find(s => s.id === stationId);
      return {
        ...state,
        stations: state.stations.map(station => 
          station.id === stationId 
            ? { ...station, enabled: !station.enabled }
            : station
        )
      };
    });

    // Call the API
    try {
      await api.toggleStation(stationId);
    } catch (error) {
      console.error('Error toggling station:', error);
      // Revert the state if the API call fails
      appStore.update(state => ({
        ...state,
        stations: state.stations.map(station => 
          station.id === stationId && previousState
            ? { ...station, enabled: previousState.enabled }
            : station
        )
      }));
    }
  },

  updateTimer: async () => {
    const state = get(appStore);
    if (!state.timerActive) return;

    let { timerHours, timerMinutes, timerSeconds } = state;
    
    if (timerSeconds > 0) {
      timerSeconds--;
    } else if (timerMinutes > 0) {
      timerMinutes--;
      timerSeconds = 59;
    } else if (timerHours > 0) {
      timerHours--;
      timerMinutes = 59;
      timerSeconds = 59;
    } else {
      appStore.update(state => ({ ...state, timerActive: false }));
      return;
    }

    // Update both frontend and backend
    try {
      await api.setTimer(timerHours, timerMinutes);
      appStore.update(state => ({ 
        ...state, 
        timerHours, 
        timerMinutes, 
        timerSeconds 
      }));
    } catch (error) {
      console.error('Error updating timer:', error);
    }
  },

  saveSettings: async (settings: Partial<AppState>) => {
    const previousState = get(appStore);
    
    appStore.update(state => ({ ...state, ...settings }));

    // Call the API
    try {
      // Extract only the system settings fields
      const systemSettings = {
        cutoffVoltage: settings.cutoffVoltage!,
        motorCurrentThreshold: settings.motorCurrentThreshold!,
        switchCurrentThreshold: settings.switchCurrentThreshold!,
        cycleLimit: settings.cycleLimit!,
        motorFailureThreshold: settings.motorFailureThreshold!,
        switchFailureThreshold: settings.switchFailureThreshold!,
        cyclesPerMinute: settings.cyclesPerMinute!
      };
      await api.updateSettings(systemSettings);
    } catch (error) {
      console.error('Error saving settings:', error);
      // Revert the state if the API call fails
      appStore.update(() => previousState);
    }
  },

  setTimer: async (hours: number, minutes: number) => {
    const previousState = get(appStore);
    
    try {
      // Call APIs first
      await api.setTimer(hours, minutes);
      if (hours > 0 || minutes > 0) {
        await api.startTest();
      }

      // Update state only after successful API calls
      appStore.update(state => ({
        ...state,
        timerHours: hours,
        timerMinutes: minutes,
        timerSeconds: 0,
        timerActive: hours > 0 || minutes > 0,
        showTimerModal: false,
        masterEnabled: (hours > 0 || minutes > 0) ? true : state.masterEnabled
      }));
    } catch (error) {
      console.error('Error setting timer:', error);
      // Revert the state if the API call fails
      appStore.update(() => previousState);
    }
  }
}; 